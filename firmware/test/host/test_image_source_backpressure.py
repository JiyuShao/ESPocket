"""Real Core image submissions: finite FIFO, nonblocking App, and instance revocation."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/firmware'))
from prepare_patched_component import prepare
CORE=ROOT/'firmware/managed_components/espressif__brookesia_system_core'
PATCHES=ROOT/'firmware/patches/espressif__brookesia_system_core/0.8.4'


def exercise(source,directory):
    text=(source/'src/system/gui.cpp').read_text()
    begin=text.find('std::expected<void, std::string> System::Impl::enqueue_gui_image_source(')
    if begin<0:begin=text.index('std::expected<void, std::string> System::gui_set_view_src(')
    methods=text[begin:text.index('std::expected<void, std::string> System::gui_preload_images(',begin)]
    header=(source/'src/private/system/impl.hpp').read_text()
    begin=header.index('    template <typename Result, typename Fn>\n    Result run_task_sync(')
    sync=header[begin:header.index('    std::expected<void, std::string> post_gui_task',begin)]
    begin=header.find('    struct PendingImageSources {')
    fields=header[begin:header.index('    gui::Runtime::ActionHandler',begin)] if begin>=0 else r'''
    struct PendingImageSources{};
    void clear_pending_gui_image_sources(unsigned){}
    void clear_all_pending_gui_image_sources(){}
'''
    code=r'''
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <deque>
#include <expected>
#include <functional>
#include <future>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <string_view>
#include <thread>
#include <vector>
using namespace std::chrono_literals;
namespace boost{template<class T>using promise=std::promise<T>;}
unsigned warnings=0;
#define BROOKESIA_LOGW(...) ++warnings
namespace esp_brookesia::system::core {
namespace gui{using DocumentId=unsigned;}
namespace lib_utils{using TaskSchedulerGroup=std::string;}
using AppId=unsigned;const std::string SYSTEM_GUI_INPUT_TASK_GROUP="gui_input";
struct System {
 struct Impl {
  struct Record{std::optional<unsigned>document_id=1;}record;
  struct Gui{std::vector<std::string>seen;bool fail=false;std::function<void()>during_apply;
   bool set_view_src(unsigned,std::string_view,std::string_view src){seen.emplace_back(src);if(during_apply){auto hook=std::move(during_apply);hook();}return !fail;}
  };std::unique_ptr<Gui>gui_runtime_=std::make_unique<Gui>();
  std::mutex mutex,gui_image_source_mutex_;std::condition_variable changed;std::deque<std::function<void()>>tasks;
  unsigned pending=0,max_pending=0;bool stopping=false,reject_post=false;std::thread worker;
  struct Scheduler {Impl*owner;bool is_running(){return true;}
   bool post(std::function<void()>fn,void*,const std::string&){return owner->post_gui_input_task(std::move(fn)).has_value();}
  };std::unique_ptr<Scheduler>task_scheduler_=std::make_unique<Scheduler>(Scheduler{this});
  bool is_current_task_domain(const std::string&){return false;}
  Impl():worker([this]{std::this_thread::sleep_for(100ms);for(;;){
   std::function<void()> task;{std::unique_lock lock(mutex);changed.wait(lock,[&]{return stopping||!tasks.empty();});if(stopping&&tasks.empty())return;task=std::move(tasks.front());tasks.pop_front();}
   task();{std::lock_guard lock(mutex);--pending;}changed.notify_all();
  }}){}
  ~Impl(){{std::lock_guard lock(mutex);stopping=true;}changed.notify_all();worker.join();}
  std::expected<Record*,std::string>get_record(AppId){return &record;}
  void flush_pending_gui_bindings(AppId){}
  std::expected<void,std::string>post_gui_input_task(std::function<void()> fn){
   {std::lock_guard lock(mutex);if(reject_post)return std::unexpected("post failed");++pending;max_pending=std::max(max_pending,pending);tasks.push_back(std::move(fn));}changed.notify_all();return {};
  }
''' + sync + fields + r'''
  std::map<AppId,std::shared_ptr<PendingImageSources>>pending_gui_image_sources_;
  void drain(){std::unique_lock lock(mutex);changed.wait(lock,[&]{return !pending;});}
 };std::unique_ptr<Impl>impl_=std::make_unique<Impl>();
 std::expected<void,std::string>gui_set_view_src(AppId,std::string_view,std::string_view);
};
''' + methods + r'''
}
int main(){using namespace esp_brookesia::system::core;
 {
  System owner;auto start=std::chrono::steady_clock::now();
  for(unsigned i=0;i<8;++i)assert(owner.gui_set_view_src(1,"/bird",std::to_string(i)));
  assert(std::chrono::steady_clock::now()-start<50ms); // GUI is blocked for 100ms.
  for(unsigned i=0;i<200;++i)assert(!owner.gui_set_view_src(1,"/bird","overflow"));
  owner.impl_->drain();assert(owner.impl_->max_pending==1);
  assert(owner.impl_->gui_runtime_->seen.size()==8);
  for(unsigned i=0;i<8;++i)assert(owner.impl_->gui_runtime_->seen[i]==std::to_string(i));
  owner.impl_->gui_runtime_->fail=true;assert(owner.gui_set_view_src(1,"/bird","bad"));owner.impl_->drain();assert(warnings==1); // Upstream submission contract reports rendering failures at the GUI owner.
  owner.impl_->record.document_id.reset();assert(!owner.gui_set_view_src(1,"/bird","unloaded"));
 }
 {
  System owner;auto&o=*owner.impl_;
  assert(owner.gui_set_view_src(1,"/bird","old-instance"));
  o.clear_pending_gui_image_sources(1); // Same retained document on reopen.
  assert(owner.gui_set_view_src(1,"/bird","new-instance"));
  o.drain();assert(o.gui_runtime_->seen==std::vector<std::string>{"new-instance"});
  std::promise<void> entered,release;auto released=release.get_future().share();
  o.post_gui_input_task([&]{entered.set_value();released.wait();});entered.get_future().wait();
  assert(owner.gui_set_view_src(1,"/bird","shutdown"));
  o.clear_all_pending_gui_image_sources();release.set_value();o.drain();assert(o.gui_runtime_->seen.size()==1);
 }
 {
  System owner;auto&o=*owner.impl_;
  o.gui_runtime_->during_apply=[&]{for(unsigned i=8;i<16;++i)assert(owner.gui_set_view_src(1,"/bird",std::to_string(i)));};
  for(unsigned i=0;i<8;++i)assert(owner.gui_set_view_src(1,"/bird",std::to_string(i)));
  o.drain();assert(o.max_pending<=2 && o.gui_runtime_->seen.size()==16);
  for(unsigned i=0;i<16;++i)assert(o.gui_runtime_->seen[i]==std::to_string(i));
 }
 {
  System owner;auto&o=*owner.impl_;
  o.reject_post=true;assert(!owner.gui_set_view_src(1,"/bird","rejected"));
  o.reject_post=false;assert(owner.gui_set_view_src(1,"/bird","retry"));o.drain();assert(o.gui_runtime_->seen==std::vector<std::string>{"retry"});
  const auto queued=o.pending;
  assert(!owner.gui_set_view_src(1,"/bird",std::string(32768,'x')));assert(o.pending==queued);
 }
}
'''
    cpp=Path(directory)/'source.cpp';binary=Path(directory)/'source';cpp.write_text(code)
    result=subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23','-pthread',str(cpp),'-o',str(binary)],capture_output=True,text=True)
    if result.returncode:raise AssertionError(result.stderr)
    return subprocess.run([str(binary)],capture_output=True,text=True,timeout=15).returncode


class ImageSourceBackpressureTest(unittest.TestCase):
    def test_slow_gui_has_finite_ordered_async_submissions_and_revocation(self):
        with tempfile.TemporaryDirectory() as directory:
            # 011 bounded allocation by blocking the App; this is the slow path.
            import json
            manifest=json.loads((PATCHES/'manifest.json').read_text())
            manifest['patches']=[p for p in manifest['patches'] if not p['file'].startswith('018-')]
            prior=Path(directory)/'prior.json';prior.write_text(json.dumps(manifest))
            for patch in manifest['patches']:
                (Path(directory)/patch['file']).write_bytes((PATCHES/patch['file']).read_bytes())
            baseline=prepare(CORE,prior,Path(directory)/'baseline')
            self.assertNotEqual(exercise(baseline,directory),0)
            candidate=prepare(CORE,PATCHES/'manifest.json',Path(directory)/'candidate')
            self.assertEqual(exercise(candidate,directory),0)

if __name__=='__main__':unittest.main()
