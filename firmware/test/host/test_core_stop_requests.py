"""Stopped Core must not retain dialog handlers into its next normal run.

Compile the actual patched stop, enqueue and validity methods. The scheduler is
synchronous here; real callback/GUI races remain device acceptance conditions.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare

class CoreStopRequestsTest(unittest.TestCase):
    def exercise(self, core):
        lifecycle = (core / 'src/system/lifecycle.cpp').read_text()
        manager = (core / 'src/app/manager.cpp').read_text()
        start_method = lifecycle[lifecycle.index('std::expected<void, std::string> System::start()'):lifecycle.index('void System::stop()')]
        stop = lifecycle[lifecycle.index('void System::stop()'):lifecycle.index('void System::deinit()')]
        enqueue = manager[manager.index('std::expected<MessageDialogRequestId, std::string> System::enqueue_message_dialog('):manager.index('std::expected<void, std::string> System::show_next_message_dialog()')]
        valid = manager[manager.index('bool System::has_message_dialog_request('):manager.index('std::expected<void, std::string> System::show_app_loading(')]
        close = manager[manager.index('std::expected<void, std::string> System::close_message_dialog('):manager.index('std::expected<void, std::string> System::update_message_dialog(')]
        keyboard = manager[manager.index('std::expected<void, std::string> System::hide_app_keyboard('):manager.index('std::expected<MessageDialogRequestId, std::string> System::show_app_message_dialog(')]
        harness = r'''
#include <cassert>
#include <algorithm>
#include <expected>
#include <functional>
#include <map>
#include <memory>
#include <optional>
#include <string>
#include <vector>
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS(...) ((void)0)
#define BROOKESIA_LOGI(...) ((void)0)
#define BROOKESIA_LOGE(...) ((void)0)
#define BROOKESIA_LOGW(...) ((void)0)
constexpr auto SYSTEM_APP_TASK_GROUP="app", SYSTEM_GUI_INPUT_TASK_GROUP="gui-input";
using AppId=int; using MessageDialogRequestId=unsigned;using KeyboardRequestId=unsigned;
struct KeyboardResult {unsigned request_id;int app_id;bool confirmed;std::string text;};
constexpr AppId INVALID_APP_ID=0;
constexpr MessageDialogRequestId INVALID_MESSAGE_DIALOG_REQUEST_ID=0;
enum class MessageDialogButtonRole {Invalid,Confirm};
enum class MessageDialogCloseReason {Button,Closed};
struct MessageDialogResult {unsigned request_id;int app_id;int button_index;MessageDialogButtonRole button_role;MessageDialogCloseReason reason;};
struct MessageDialogOptions {struct Button {MessageDialogButtonRole role;};std::vector<Button> buttons;};
using MessageDialogResultHandler=std::function<void(int)>;
bool is_blocking_runtime_service_call_context(){return false;}
struct System {
 struct Request {MessageDialogRequestId request_id;AppId app_id;MessageDialogOptions options;MessageDialogResultHandler handler;};
 struct KeyboardRecord {unsigned request_id;int app_id;std::function<void(KeyboardResult)> handler;};
 struct Impl {
  using MessageDialogRequestRecord=Request;
  bool started_=true,initialized_=true,stop_cleanup_failed_=false,reject=false;
  unsigned next_message_dialog_request_id_=1;
  std::map<unsigned,Request> message_dialog_requests_;
  std::map<unsigned,KeyboardRecord> keyboard_requests_;
  struct Service {void publish_keyboard_closed(KeyboardResult){}};std::shared_ptr<Service> system_service_;
  std::vector<unsigned> queued_message_dialog_requests_;
  std::optional<unsigned> active_message_dialog_request_id_;
  unsigned drains=0;
  bool should_schedule_app_task(){return false;}
  bool should_defer_gui_task(auto){return false;}
  std::expected<void,std::string> post_gui_input_task(auto fn){fn();return {};}
  template<class R,class F>R run_task_sync(auto,F fn,R rejected){return reject?rejected:fn();}
  void advance_app_starts(bool){++drains;}
  void hide_startup_overlay(){}
  std::expected<void,std::string> get_record(AppId){return {};}
 } backing;
 Impl* impl_=&backing;
 unsigned shown=0,stops=0,published=0,hidden=0;
 void on_hide_message_dialog(AppId,unsigned){++hidden;}
 std::expected<void,std::string> show_next_message_dialog(){return {};}
 void remove_queued_message_dialog(unsigned id){auto &q=backing.queued_message_dialog_requests_;q.erase(std::remove(q.begin(),q.end(),id),q.end());}
 void publish_message_dialog_closed(MessageDialogResult result,MessageDialogResultHandler handler){++published;if(handler)handler(result.button_index);}
 std::expected<void,std::string> close_message_dialog(AppId,unsigned,int,MessageDialogCloseReason,bool,bool);
 void on_stop(){++stops;}
 void on_hide_app_keyboard(AppId,unsigned){++hidden;}
 std::expected<void,std::string> hide_app_keyboard(AppId,unsigned);
 std::expected<void,std::string> complete_app_keyboard(AppId,unsigned,bool,std::string);
 std::expected<void,std::string> on_show_message_dialog(AppId,unsigned,const MessageDialogOptions&){++shown;return {};}
 void stop();
 std::expected<void,std::string> start();
 std::expected<void,std::string> on_start(){return {};}
 void deinit(){}
 bool has_message_dialog_request(AppId,unsigned);
 std::expected<unsigned,std::string> enqueue_message_dialog(AppId,bool,MessageDialogOptions,MessageDialogResultHandler);
};
''' + start_method + stop + enqueue + valid + close + keyboard + r'''
int main(){
 System s;
 for(unsigned round=0;round<3;++round){
  auto lifetime=std::make_shared<int>(1);std::weak_ptr<int> observed=lifetime;
  auto active=s.enqueue_message_dialog(0,false,{},[lifetime](int){});
  auto queued=s.enqueue_message_dialog(0,false,{},[lifetime](int){});
  assert(active && queued && *active!=*queued);
  assert(s.has_message_dialog_request(0,*active));
  assert(s.backing.queued_message_dialog_requests_.size()==1);
  lifetime.reset();assert(!observed.expired());
  s.backing.keyboard_requests_.emplace(99,System::KeyboardRecord{99,1,{}});
  s.stop();
  assert(s.backing.message_dialog_requests_.empty() && "stop retained old system dialog handlers");
  assert(s.backing.queued_message_dialog_requests_.empty());
  assert(s.backing.keyboard_requests_.empty());
  assert(!s.backing.active_message_dialog_request_id_);
  assert(observed.expired() && "stopped handler still retains its owner");
  assert(!s.has_message_dialog_request(0,*active));
  assert(!s.close_message_dialog(0,*active,0,MessageDialogCloseReason::Button,true,true));
  assert(!s.close_message_dialog(0,*queued,-1,MessageDialogCloseReason::Closed,true,true));
  s.stop();assert(s.stops==round+1);
  // Model the next successful product start, without resetting request IDs.
  s.backing.started_=true;
  auto fresh=s.enqueue_message_dialog(0,false,{},{});
  assert(fresh && *fresh>*queued && s.has_message_dialog_request(0,*fresh));
  assert(!s.has_message_dialog_request(0,*active));
  assert(!s.close_message_dialog(0,*active,0,MessageDialogCloseReason::Button,true,true));
  assert(s.has_message_dialog_request(0,*fresh) && s.published==0 && s.hidden==0);
  s.backing.message_dialog_requests_.clear();s.backing.active_message_dialog_request_id_.reset();
 }
 assert(s.shown==6 && s.backing.drains==3);
 System rejected;
 auto old=rejected.enqueue_message_dialog(0,false,{},{});assert(old);
 unsigned keyboard_deliveries=0;
 rejected.backing.keyboard_requests_.emplace(99,System::KeyboardRecord{99,1,[&](KeyboardResult){++keyboard_deliveries;}});
 rejected.backing.reject=true;rejected.stop();
 assert(!rejected.start() && "rejected cleanup must block restart with retained requests");
 assert(rejected.backing.message_dialog_requests_.size()==1);
 assert(!rejected.has_message_dialog_request(0,*old));
 assert(!rejected.close_message_dialog(0,*old,0,MessageDialogCloseReason::Button,true,true));
 assert(rejected.published==0 && rejected.hidden==0);
 assert(!rejected.complete_app_keyboard(1,99,true,"late") && "stopped keyboard completion must not reach its handler");
 assert(!rejected.hide_app_keyboard(1,99));assert(keyboard_deliveries==0);


}
'''
        with tempfile.TemporaryDirectory(prefix='core-stop-requests-run-') as directory:
            cpp=Path(directory)/'test.cpp';binary=Path(directory)/'test'
            cpp.write_text(harness)
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23',str(cpp),'-o',str(binary)],check=True)
            return subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)

    def test_stop_revokes_active_queued_requests_and_handler_lifetimes(self):
        with tempfile.TemporaryDirectory(prefix='core-stop-requests-') as directory:
            core=prepare(ROOT/'firmware/managed_components/espressif__brookesia_system_core',
                         ROOT/'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json',
                         Path(directory)/'core')
            result=self.exercise(core)
            self.assertEqual(result.returncode,0,result.stderr)
