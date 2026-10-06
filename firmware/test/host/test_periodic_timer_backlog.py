"""Exercise periodic enqueue and real dispatch with a callback crossing the next due time."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare
SOURCE = ROOT / 'firmware/managed_components/espressif__brookesia_system_core'
MANIFEST = ROOT / 'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json'


def exercise(source, directory):
    text = (source / 'src/system/timer.cpp').read_text()
    start = text.index('std::expected<void, std::string> System::Impl::dispatch_timer(')
    methods = text[start:text.index('std::expected<TimerId, std::string> System::timer_start_delayed(', start)]
    code = r'''
#include <algorithm>
#include <cassert>
#include <deque>
#include <expected>
#include <functional>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <string_view>
#include <variant>
#include <vector>
#define BROOKESIA_SYSTEM_CORE_ENABLE_PROFILE_LOG 0
#define BROOKESIA_LOGW(...) ((void)0)
using AppId=int;using TimerId=int;constexpr TimerId INVALID_TIMER_ID=0;
constexpr char SYSTEM_APP_TASK_GROUP[]="app",SYSTEM_TIMER_TASK_GROUP[]="timer",LIFECYCLE_ON_TIMER[]="on_timer";
namespace lib_utils { struct FunctionGuard {std::function<void()> f;FunctionGuard(std::function<void()> f):f(f){}~FunctionGuard(){f();}}; }
enum class AppState {Running,Stopped};enum class AppKind {Native,Runtime};
struct Context {};
struct Native {std::function<std::expected<void,std::string>()> callback;auto on_timer(Context&,int,std::string){return callback();}};
struct Scheduler {std::function<bool()> fire;int next=1;
 bool post_periodic(std::function<bool()> f,int,TimerId*out,const char*){fire=f;*out=next++;return true;}
};
struct System {
 struct Impl {
  struct PendingTimer {int app_id,timer_id;std::string name;};
  struct AppRecord {struct TimerRecord{std::string name;bool periodic;};
   struct {int app_id=1;AppState state=AppState::Running;struct{AppKind kind=AppKind::Native;}manifest;}info;
   std::map<int,TimerRecord> timers;std::shared_ptr<Native>native_app=std::make_shared<Native>();std::shared_ptr<Context>context=std::make_shared<Context>();
  }record;
  std::shared_ptr<Scheduler>task_scheduler_=std::make_shared<Scheduler>();std::mutex timer_mutex_;std::recursive_mutex timer_map_mutex_;
  std::vector<PendingTimer>pending_timers_;std::deque<std::function<void()>>queued;bool fail_post=false;
  std::expected<AppRecord*,std::string>get_record(AppId){return &record;}
  std::expected<void,std::string>post_task(const char*,std::function<void()>f){if(fail_post)return std::unexpected("post");queued.push_back(f);return {};}
  std::expected<void,std::string>dispatch_timer(AppId,TimerId,std::string);
  std::expected<void,std::string>call_runtime_lifecycle(AppRecord&r,const char*,std::initializer_list<std::variant<double,std::string>>){return r.native_app->callback();}
 };
 std::unique_ptr<Impl>impl_=std::make_unique<Impl>();
 std::expected<TimerId,std::string>timer_start_periodic(AppId,std::string_view,int);
};
''' + methods + r'''
int main(){
 System system;auto &s=*system.impl_;int callbacks=0,active=0,maximum_active=0;
 s.record.native_app->callback=[&]()->std::expected<void,std::string>{
  ++active;maximum_active=std::max(maximum_active,active);++callbacks;
  if(callbacks==1){for(int i=0;i<8;++i)assert(s.task_scheduler_->fire());
   assert(s.queued.size()==1 && s.pending_timers_.size()==1);}
  --active;return {};
 };
 const auto id=system.timer_start_periodic(1,"game",33);assert(id);
 assert(s.task_scheduler_->fire());assert(s.queued.size()==1);
 auto run=[&]{auto f=std::move(s.queued.front());s.queued.pop_front();f();};
 run();assert(callbacks==1 && s.queued.size()==1 && s.pending_timers_.size()==1);
 run();assert(callbacks==2 && s.queued.empty() && s.pending_timers_.empty() && maximum_active==1);
 assert(s.task_scheduler_->fire());s.record.timers.clear();run();assert(callbacks==2); // Stop revokes queued delivery.
 assert(s.pending_timers_.empty());
 const auto replacement=system.timer_start_periodic(1,"replacement",33);assert(replacement && *replacement!=*id);
 s.record.info.manifest.kind=AppKind::Runtime;
 assert(s.task_scheduler_->fire());s.fail_post=true;run();assert(callbacks==3);
 assert(!s.task_scheduler_->fire());assert(s.pending_timers_.empty());
}
'''
    directory = Path(directory)
    cpp, binary = directory / 'timer.cpp', directory / 'timer'
    cpp.write_text(code)
    subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(cpp), '-o', str(binary)], check=True)
    return subprocess.run([str(binary)], capture_output=True, timeout=10)


class PeriodicTimerBacklogTest(unittest.TestCase):
    def test_one_queued_due_callback_while_current_callback_executes(self):
        with tempfile.TemporaryDirectory(prefix='espocket-periodic-backlog-') as d:
            self.assertNotEqual(exercise(SOURCE, d).returncode, 0)
            patched = prepare(SOURCE, MANIFEST, Path(d) / 'patched')
            result = exercise(patched, d)
            self.assertEqual(result.returncode, 0, result.stderr)
