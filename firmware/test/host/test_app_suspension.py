"""Execute the production Core suspension/activity methods with App callbacks as boundary doubles."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class AppSuspensionTest(unittest.TestCase):
    def test_overlapping_reasons_revocation_failure_and_activity(self):
        with tempfile.TemporaryDirectory(prefix='app-suspension-') as d:
            work = Path(d)
            core = prepare(ROOT / 'firmware/managed_components/espressif__brookesia_system_core',
                           ROOT / 'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json', work / 'core')
            source = (core / 'src/app/manager.cpp').read_text()
            start = source.index('std::optional<AppExecutionState> System::app_execution_state(')
            methods = source[start:source.index('std::expected<void, std::string> System::request_close_app(', start)]
            types = (core / 'include/brookesia/system_core/app/types.hpp').read_text()
            state = types[types.index('struct AppPauseReasons {'):types.index('struct AppInfo {')]
            cpp = work / 'test.cpp'
            cpp.write_text(r'''
#include <cassert>
#include <cstdint>
#include <expected>
#include <functional>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>
#include <variant>
using AppId=int;constexpr int SYSTEM_APP_TASK_GROUP=1;
enum class AppKind{Native,Runtime};enum class AppState{Installed,Starting,Running,Paused,Stopped,Error};
''' + state + r'''
struct Context{};
struct Native {
 std::vector<std::string> calls;std::vector<AppPauseReasons> reasons;std::string fail;std::function<void(std::string_view)> callback;
 std::expected<void,std::string> call(std::string name){calls.push_back(name);if(callback)callback(name);if(fail==name)return std::unexpected(name+" failed");return {};}
 auto on_pause(Context&){return call("pause");}auto on_resume(Context&){return call("resume");}
 auto on_pause_reasons_changed(Context&,const AppPauseReasons&r){reasons.push_back(r);return call("change");}
};
struct Record{
 struct Info{struct Manifest{AppKind kind=AppKind::Native;}manifest;AppState state=AppState::Running;std::string last_error;}info;
 AppExecutionState execution{.instance=11};bool pending_start=false;
 std::shared_ptr<Native>native_app=std::make_shared<Native>();std::shared_ptr<Context>context=std::make_shared<Context>();
};
struct Impl{
 Record record;int active_app_id_=7;bool missing=false,schedule=false,reject=false;
 struct Config{std::function<std::optional<uint64_t>(AppId)>native_pointer_access;std::function<void(AppId)>user_activity;}config_;
 bool should_schedule_app_task(){return schedule;}
 template<class R,class F>R run_task_sync(int,F f,R failure){if(reject)return failure;schedule=false;return f();}
 std::expected<Record*,std::string>get_record(int){if(missing)return std::unexpected("gone");return &record;}
 std::expected<void,std::string>call_runtime_lifecycle(Record&r,std::string_view method,std::initializer_list<std::variant<bool>> = {}){
  return r.native_app->call(method=="on_pause"?"pause":method=="on_resume"?"resume":"change");
 }
 auto call_runtime_pause_reasons_changed(Record&r,const AppPauseReasons&reasons){return r.native_app->on_pause_reasons_changed(*r.context,reasons);}
};
struct System{
 Impl backing;Impl*impl_=&backing;
 std::optional<AppExecutionState>app_execution_state(AppId);
 bool report_app_user_activity(AppId,uint64_t,uint64_t);
 std::expected<void,std::string>set_app_suspension(AppId,uint64_t,bool,bool);
 std::expected<void,std::string>pause_app(AppId);std::expected<void,std::string>resume_app(AppId);
 std::expected<void,std::string>apply_app_suspension(AppId,uint64_t,bool,bool,bool);
};
''' + methods + r'''
int main(){
 for(auto kind:{AppKind::Native,AppKind::Runtime}){
  System s;auto&b=s.backing;auto&r=b.record;r.info.manifest.kind=kind;auto app=r.native_app;
  uint64_t epoch=5;int activity=0;b.config_.native_pointer_access=[&](int)->std::optional<uint64_t>{return epoch;};
  b.config_.user_activity=[&](int){++activity;};
  assert(s.report_app_user_activity(7,11,5));assert(activity==1);
  assert(s.set_app_suspension(7,11,true,false));assert(r.info.state==AppState::Paused);
  assert(app->calls==std::vector<std::string>({"pause","change"}));assert(!s.app_execution_state(7)->activity_epoch);
  assert(s.set_app_suspension(7,11,true,false));assert(app->calls.size()==2);
  assert(s.set_app_suspension(7,11,true,true));assert(app->calls.back()=="change");assert(app->calls.size()==3);
  assert(app->reasons.back().covered && app->reasons.back().screen_off && !app->reasons.back().manual_pause);
  assert(s.set_app_suspension(7,11,true,false));assert(app->calls.size()==4); // wake while covered
  assert(!s.report_app_user_activity(7,11,5));
  assert(s.set_app_suspension(7,11,false,false));assert(app->calls.back()=="resume" && app->calls.size()==6);
  assert(s.set_app_suspension(7,11,false,false));assert(app->calls.size()==6);
  epoch=6;assert(!s.report_app_user_activity(7,11,5));assert(s.report_app_user_activity(7,11,6));
  assert(s.pause_app(7));assert(s.set_app_suspension(7,11,true,false));assert(s.resume_app(7));
  assert(r.info.state==AppState::Paused);assert(s.set_app_suspension(7,11,false,false));assert(r.info.state==AppState::Running);
  auto calls=app->calls.size();b.active_app_id_=8;assert(!s.set_app_suspension(7,11,true,false));assert(!s.resume_app(7));
  assert(!s.report_app_user_activity(7,11,6));assert(app->calls.size()==calls);assert(b.active_app_id_==8);
  b.active_app_id_=7;r.info.state=AppState::Stopped;assert(!s.resume_app(7));assert(!s.app_execution_state(7));
  r.info.state=AppState::Running;r.execution={.instance=12};assert(!s.set_app_suspension(7,11,false,false));
  assert(!s.report_app_user_activity(7,11,6));assert(app->calls.size()==calls);
  // Callback stops/replaces the instance: no second notification or resume writes it back.
  app->callback=[&](std::string_view){r.info.state=AppState::Stopped;};
  assert(!s.set_app_suspension(7,12,true,false));assert(r.info.state==AppState::Stopped);
 }
 for(auto failure:{"pause","change","resume"}){
  System s;auto&r=s.backing.record;auto app=r.native_app;
  if(std::string(failure)=="resume")assert(s.set_app_suspension(7,11,true,false));
  app->fail=failure;
  assert(!s.set_app_suspension(7,11,std::string(failure)!="resume",false));
  assert(r.info.state==AppState::Paused && r.execution.lifecycle_failed && !r.info.last_error.empty());
  auto calls=app->calls.size();assert(!s.set_app_suspension(7,11,false,false));assert(app->calls.size()==calls);
 }
 // Reason callbacks may reenter and add a new cause BEFORE resume.
 for(auto kind:{AppKind::Native,AppKind::Runtime}){
  System reason_nested;auto&r=reason_nested.backing.record;r.info.manifest.kind=kind;
  assert(reason_nested.set_app_suspension(7,11,true,false));
  bool recursed=false;r.native_app->callback=[&](std::string_view method){
   if(method=="change"&&!recursed){recursed=true;assert(reason_nested.set_app_suspension(7,11,true,false));}
  };
  assert(reason_nested.set_app_suspension(7,11,false,false));
  assert(r.info.state==AppState::Paused && r.execution.covered);
  assert(r.native_app->calls==std::vector<std::string>({"pause","change","change","change"}));
 }
 // Snapshot reflects delivery-time facts after a reentrant pause callback.
 System snapshot;bool added=false;auto&snap=snapshot.backing.record;
 snap.native_app->callback=[&](std::string_view method){
  if(method=="pause"&&!added){added=true;assert(snapshot.set_app_suspension(7,11,true,true));}
 };
 assert(snapshot.set_app_suspension(7,11,true,false));
 assert(snap.native_app->reasons.back().covered && snap.native_app->reasons.back().screen_off);
 // Foreground revocation within the reason callback prevents resume side effects.
 System switched;assert(switched.set_app_suspension(7,11,true,false));
 switched.backing.record.native_app->callback=[&](std::string_view method){
  if(method=="change")switched.backing.active_app_id_=8;
 };
 assert(!switched.set_app_suspension(7,11,false,false));
 assert(switched.backing.record.native_app->calls.back()=="change");
 // Exceptions and a nested new cover during resume remain fail-closed.
 System thrown;thrown.backing.record.native_app->callback=[](std::string_view){throw std::runtime_error("failure");};
 assert(!thrown.set_app_suspension(7,11,true,false));assert(thrown.backing.record.execution.lifecycle_failed);
 System nested;assert(nested.set_app_suspension(7,11,true,false));
 nested.backing.record.native_app->callback=[&](std::string_view method){
  if(method=="resume")assert(nested.set_app_suspension(7,11,true,false));
 };
 assert(!nested.set_app_suspension(7,11,false,false));
 assert(nested.backing.record.info.state==AppState::Paused && nested.backing.record.execution.covered);
 System s;s.backing.schedule=true;s.backing.reject=true;
 assert(!s.set_app_suspension(7,11,true,false));assert(s.backing.record.info.state==AppState::Running);
 assert(!s.report_app_user_activity(7,11,5));
}
''')
            binary = work / 'test'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(cpp), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=10)

if __name__ == '__main__':
    unittest.main()
