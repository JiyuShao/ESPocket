"""Exercise real Core source updates with a slow GUI owner and finite task budget."""
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
    begin=text.index('std::expected<void, std::string> System::gui_set_view_src(')
    method=text[begin:text.index('std::expected<void, std::string> System::gui_preload_images(',begin)]
    header=(source/'src/private/system/impl.hpp').read_text()
    begin=header.index('    template <typename Result, typename Fn>\n    Result run_task_sync(')
    sync=header[begin:header.index('    std::expected<void, std::string> post_gui_task',begin)]
    code=r'''
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <deque>
#include <expected>
#include <functional>
#include <future>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <string_view>
#include <thread>
#include <vector>
using namespace std::chrono_literals;
namespace boost{template<class T>using promise=std::promise<T>;}
#define BROOKESIA_LOGW(...)
namespace esp_brookesia::system::core {
namespace lib_utils{using TaskSchedulerGroup=std::string;}
using AppId=unsigned;const std::string SYSTEM_GUI_INPUT_TASK_GROUP="gui_input";
struct System {
 struct Impl {
  struct Record{std::optional<unsigned>document_id=1;}record;
  struct Gui{std::vector<std::string>seen;bool fail=false;
   bool set_view_src(unsigned,std::string_view,std::string_view src){seen.emplace_back(src);return !fail;}
  };std::unique_ptr<Gui>gui_runtime_=std::make_unique<Gui>();
  std::mutex mutex;std::condition_variable changed;std::deque<std::function<void()>>tasks;
  unsigned pending=0,max_pending=0;bool stopping=false;std::thread worker;
  struct Scheduler {Impl*owner;bool is_running(){return true;}
   bool post(std::function<void()>fn,void*,const std::string&){return owner->post_gui_input_task(std::move(fn)).has_value();}
  };std::unique_ptr<Scheduler>task_scheduler_=std::make_unique<Scheduler>(Scheduler{this});
  bool is_current_task_domain(const std::string&){return false;}
  Impl():worker([this]{std::this_thread::sleep_for(20ms);for(;;){
   std::function<void()> task;{std::unique_lock lock(mutex);changed.wait(lock,[&]{return stopping||!tasks.empty();});if(stopping&&tasks.empty())return;task=std::move(tasks.front());tasks.pop_front();}
   task();{std::lock_guard lock(mutex);--pending;}changed.notify_all();
  }}){}
  ~Impl(){{std::lock_guard lock(mutex);stopping=true;}changed.notify_all();worker.join();}
  std::expected<Record*,std::string>get_record(AppId){return &record;}
  void flush_pending_gui_bindings(AppId){}
  std::expected<void,std::string>post_gui_input_task(std::function<void()> fn){
   {std::lock_guard lock(mutex);++pending;max_pending=std::max(max_pending,pending);tasks.push_back(std::move(fn));}changed.notify_all();return {};
  }
''' + sync + r'''
  void drain(){std::unique_lock lock(mutex);changed.wait(lock,[&]{return !pending;});}
 };std::unique_ptr<Impl>impl_=std::make_unique<Impl>();
 std::expected<void,std::string>gui_set_view_src(AppId,std::string_view,std::string_view);
};
''' + method + r'''
}
int main(){using namespace esp_brookesia::system::core;System owner;
 for(unsigned i=0;i<200;++i)assert(owner.gui_set_view_src(1,"/bird",std::to_string(i)));
 owner.impl_->drain();assert(owner.impl_->max_pending<=2);
 assert(owner.impl_->gui_runtime_->seen.size()==200);
 for(unsigned i=0;i<200;++i)assert(owner.impl_->gui_runtime_->seen[i]==std::to_string(i));
 owner.impl_->gui_runtime_->fail=true;assert(!owner.gui_set_view_src(1,"/bird","bad"));
 owner.impl_->record.document_id.reset();assert(!owner.gui_set_view_src(1,"/bird","unloaded"));
}
'''
    cpp=Path(directory)/'source.cpp';binary=Path(directory)/'source';cpp.write_text(code)
    result=subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23','-pthread',str(cpp),'-o',str(binary)],capture_output=True,text=True)
    if result.returncode:raise AssertionError(result.stderr)
    return subprocess.run([str(binary)],capture_output=True,text=True,timeout=15).returncode


class ImageSourceBackpressureTest(unittest.TestCase):
    def test_slow_gui_cannot_accumulate_source_tasks_or_lose_order_and_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertNotEqual(exercise(CORE,directory),0)
            candidate=prepare(CORE,PATCHES/'manifest.json',Path(directory)/'candidate')
            self.assertEqual(exercise(candidate,directory),0)

if __name__=='__main__':unittest.main()
