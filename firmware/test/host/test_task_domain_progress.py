"""Real Core group guards and Boost strands must leave a worker for unrelated timers."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare
CORE = ROOT / 'firmware/managed_components/espressif__brookesia_system_core'
PATCHES = ROOT / 'firmware/patches/espressif__brookesia_system_core/0.8.4'
BOOST = ROOT / 'firmware/managed_components/espressif__esp-boost/src'


def exercise(source, directory):
    text = (source / 'src/system/task.cpp').read_text()
    start = text.index('lib_utils::TaskScheduler::GroupConfig System::Impl::make_task_group_config(')
    methods = text[start:text.index('bool System::Impl::should_schedule_app_task()', start)]
    scheduler = (ROOT / 'firmware/managed_components/espressif__brookesia_lib_utils/src/task_scheduler.cpp').read_text()
    start = scheduler.index('bool TaskScheduler::Impl::configure_group(')
    configure = scheduler[start:scheduler.index('bool TaskScheduler::Impl::wait_tasks_internal(', start)]
    code = r'''
#include <boost/asio.hpp>
#include <cassert>
#include <chrono>
#include <functional>
#include <future>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <thread>
using namespace std::chrono_literals;
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS()
#define BROOKESIA_LOGD(...)
#define BROOKESIA_DESCRIBE_TO_STR(...)
#define BROOKESIA_CHECK_FALSE_RETURN(test, result, ...) if (!(test)) return result
namespace boost { using mutex=std::mutex; template<class T> using lock_guard=std::lock_guard<T>; }
namespace esp_brookesia::lib_utils {
struct TaskScheduler {
 using Group=std::string;using TaskId=int;using TaskType=int;
 using Pre=std::function<void(const Group&,TaskId,TaskType)>;
 using Post=std::function<void(const Group&,TaskId,TaskType,bool)>;
 struct GroupConfig { bool enable_serial_execution=false; Group parent_group; Pre pre_execute_callback; Post post_execute_callback; };
 struct Impl {
  std::shared_ptr<boost::asio::io_context> io_context_=std::make_shared<boost::asio::io_context>();
  std::map<Group,std::shared_ptr<boost::asio::strand<boost::asio::io_context::executor_type>>> strands_;
  std::map<Group,Pre> pre_execute_callbacks_;std::map<Group,Post> post_execute_callbacks_;
  boost::mutex mutex_;bool is_running(){return true;}bool configure_group(const Group&,const GroupConfig&);
 } impl;
 bool is_running(){return true;}
 bool configure_group(const Group&g,const GroupConfig&c){return impl.configure_group(g,c);}
 std::promise<void>*child_entered=nullptr;
 void post(const Group&g,std::function<void()> task) {
  boost::asio::post(*impl.strands_.at(g),[this,g,task]{
   if(g=="app_input" || g=="gui_input") child_entered->set_value();
   impl.pre_execute_callbacks_.at(g)(g,0,0);task();impl.post_execute_callbacks_.at(g)(g,0,0,true);
  });
 }
};
''' + configure + r'''
}
namespace esp_brookesia::system::core {
namespace lib_utils=esp_brookesia::lib_utils;
const std::string SYSTEM_GUI_TASK_GROUP="gui",SYSTEM_GUI_INPUT_TASK_GROUP="gui_input",SYSTEM_APP_TASK_GROUP="app",SYSTEM_APP_INPUT_TASK_GROUP="app_input",SYSTEM_TIMER_TASK_GROUP="timer";
thread_local const void*current_system_task_owner=nullptr;thread_local std::string current_system_task_group;
struct System { struct Impl {
 std::shared_ptr<lib_utils::TaskScheduler> task_scheduler_=std::make_shared<lib_utils::TaskScheduler>();
 std::recursive_mutex gui_runtime_mutex_,app_callback_mutex_;
 struct Guard {std::function<void()> lock,unlock;};std::optional<Guard> gui_thread_guard_;
 lib_utils::TaskScheduler::GroupConfig make_task_group_config(const std::string&,bool=false,bool=false,bool=false);
 bool configure_task_groups();
};};
''' + methods + r'''
}
int main() {
 for (bool gui:{false,true}) {
  using namespace esp_brookesia::system::core;
  System::Impl owner;assert(owner.configure_task_groups());auto&s=*owner.task_scheduler_;
  std::promise<void> started,release,child_entered,timer;auto released=release.get_future().share();
  auto child_start=child_entered.get_future();auto timer_ready=timer.get_future();s.child_entered=&child_entered;
  std::vector<int> order;
  s.post(gui?"gui":"app",[&]{assert(current_system_task_owner==&owner);started.set_value();released.wait();order.push_back(1);});
  auto work=boost::asio::make_work_guard(*s.impl.io_context_);
  std::thread first([&]{s.impl.io_context_->run();}),second([&]{s.impl.io_context_->run();});
  started.get_future().wait();
  s.post(gui?"gui_input":"app_input",[&]{assert(current_system_task_owner==&owner);order.push_back(2);});
  // In the old configuration the second worker enters a callback then blocks
  // on the domain gate. A shared strand keeps that callback in the queue.
  child_start.wait_for(100ms);
  s.post("timer",[&]{timer.set_value();});
  const bool progressed=timer_ready.wait_for(100ms)==std::future_status::ready;
  release.set_value();work.reset();first.join();second.join();
  assert(order==std::vector<int>({1,2}));assert(progressed);
 }
}
'''
    cpp = Path(directory) / 'domain.cpp'; binary = Path(directory) / 'domain'
    cpp.write_text(code)
    result = subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread', '-DBOOST_NO_USER_CONFIG', '-I', str(BOOST), str(cpp), '-o', str(binary)], capture_output=True, text=True)
    if result.returncode: raise AssertionError(result.stderr)
    return subprocess.run([str(binary)], capture_output=True, timeout=10).returncode


class TaskDomainProgressTest(unittest.TestCase):
    def test_timer_progress_while_domain_callback_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertNotEqual(exercise(CORE, d), 0)
            candidate = prepare(CORE, PATCHES / 'manifest.json', Path(d) / 'candidate')
            self.assertEqual(exercise(candidate, d), 0)

if __name__ == '__main__': unittest.main()
