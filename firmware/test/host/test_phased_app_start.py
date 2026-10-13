"""Execute real Core startup progression with delayed GUI and injected failures."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]


class PhasedAppStartTest(unittest.TestCase):
    def test_wait_cancel_failure_and_new_instance(self):
        sys.path.insert(0, str(ROOT/'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='espocket-start-progress-') as directory:
            root=Path(directory)
            core=prepare(ROOT/'firmware/managed_components/espressif__brookesia_system_core',
                         ROOT/'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json',root/'core')
            header=(core/'src/private/system/impl.hpp').read_text()
            pending=header[header.index('    enum class AppStartFailureKind'):header.index('    struct AppRecord {')]
            pending=pending.replace('boost::unique_future','std::future')
            source=(core/'src/app/start_progress.cpp').read_text()
            source='\n'.join(line for line in source.splitlines() if not line.startswith('#include'))
            source=source.replace('boost::','std::')
            manager=(core/'src/app/manager.cpp').read_text()
            synchronous=manager[manager.index('std::expected<void, std::string> System::start_app(AppId app_id)'):manager.index('std::expected<void, std::string> System::stop_app(AppId app_id)')]
            operations=manager[manager.index('void System::Impl::report_app_start_failure'):manager.index('std::expected<void, std::string> System::Impl::prepare_app_start_gui')]
            begin=manager.index('    if (record.pending_start) {',manager.index('System::stop_app('))
            end=manager.index('    if (record.info.state == AppState::Stopped',begin)
            cancel=manager[begin:end]
            harness=r'''
#include <cassert>
#include <chrono>
#include <expected>
#include <exception>
#include <functional>
#include <future>
#include <map>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
using Result=std::expected<void,std::string>;
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS() ((void)0)
#define BROOKESIA_LOGW(...) ((void)0)
#define BROOKESIA_LOGI(...) ((void)0)
#define SYSTEM_CORE_PROFILE_LOGI(...) ((void)0)
std::string failure,dialog_kind,dialog_detail;
using SteadyClock=std::chrono::steady_clock;using SteadyTimePoint=SteadyClock::time_point;
long elapsed_ms_since(SteadyTimePoint,SteadyTimePoint=SteadyClock::now()){return 0;}
namespace heap_trace {constexpr bool enabled=false;int capture(){return 0;}template<class...T>void log(T...){} }
namespace lib_utils {struct FunctionGuard {std::function<void()> fn;template<class F>FunctionGuard(F f):fn(f){}~FunctionGuard(){if(fn)fn();}void release(){fn={};}};}

constexpr int SYSTEM_APP_TASK_GROUP=1,SYSTEM_GUI_TASK_GROUP=2;
const char* LIFECYCLE_ON_START="on_start";const char* LIFECYCLE_ON_STOP="on_stop";
namespace esp_brookesia::system::core {
using AppId=int;constexpr int INVALID_APP_ID=0;
enum class AppKind {Native,Runtime};
enum class AppState {Installed,Starting,Running,Paused,Stopping,Stopped,Error};
struct AppStartOptions {};
struct Manifest {AppKind kind=AppKind::Runtime;std::string app_path="app",id="fixture";};
struct AppInfo {AppId app_id;Manifest manifest;AppState state=AppState::Installed;std::string last_error;};
struct Policy {bool enforce=true;};
std::expected<int,std::string> validate_installed_runtime_package(const std::string&,const std::string&,const Policy&){if(failure=="admission" || failure=="developer_mode_required")return std::unexpected(failure);return 1;}
namespace service {struct ServiceManager {static ServiceManager& get_instance(){static ServiceManager m;return m;}};}
namespace detail {
struct Requirement {std::string name,version;};
struct ServiceFailure {bool registered=false;std::string local_version,reason;Requirement requirement;};
std::vector<ServiceFailure> evaluate_service_requirements(const Manifest&,service::ServiceManager&){return failure=="services"?std::vector<ServiceFailure>{ServiceFailure{}}:std::vector<ServiceFailure>{};}
std::string format_service_requirement_failures(const std::vector<ServiceFailure>&){return "services";}
void release_runtime_dataflow_operations(const std::optional<int>&){}
}
struct Runtime {Result start_app(int){return failure=="runtime_start"?Result(std::unexpected(failure)):Result{};}};
struct Context {};
struct Native {int starts=0,stops=0;Result on_start(Context&){++starts;if(failure=="both")return std::unexpected("start-error");return failure=="lifecycle"?Result(std::unexpected(failure)):Result{};}Result on_stop(Context&){++stops;if(failure=="both")return std::unexpected("stop-error");return failure=="stop"?Result(std::unexpected(failure)):Result{};}};
struct Scheduler {bool allow=true;std::vector<std::function<void()>> queued;
 template<class F,class...T>bool post_delayed(F,T...){return false;}
 bool is_running(){return true;}
 bool post(std::function<void()> cb,void*,int group){assert(group==SYSTEM_GUI_TASK_GROUP);if(!allow)return false;queued.push_back(std::move(cb));return true;}
 void run(){auto old=std::move(queued);queued.clear();for(auto &cb:old)cb();}
};
struct System {
 struct Impl;Impl* impl_;int started=0,stopped=0,failed=0;
 std::string get_system_type(){return "host";}
 Result request_app_start(AppId);Result stop_app(AppId);Result start_app(AppId);Result start_app(AppId,const AppStartOptions&);
 Result on_app_started(const AppInfo& i){assert(i.state==AppState::Running);++started;return failure=="commit"?Result(std::unexpected(failure)):Result{};}
 void on_app_stopped(const AppInfo& i){assert(i.state==AppState::Stopped);++stopped;}
 void on_app_stop_failed(const AppInfo& i,const std::string&){assert(i.state==AppState::Error);++failed;}
 void on_app_start_failed(const AppInfo& i,const std::string&){assert(i.state==AppState::Error || i.state==AppState::Installed);++failed;}
};
void show_app_admission_error_dialog(System&,const AppInfo&,std::string_view e){dialog_kind="admission";dialog_detail=e;}
void show_lifecycle_error_dialog(System&,const AppInfo&,const char*,const char*,const std::string&e){dialog_kind="lifecycle";dialog_detail=e;}
struct System::Impl {
''' + pending + r'''
 struct AppRecord {struct{uint64_t instance=0;}execution;AppInfo info;std::shared_ptr<PendingAppStart> pending_start;std::shared_ptr<Native> native_app=std::make_shared<Native>();std::shared_ptr<Context> context=std::make_shared<Context>();std::optional<int> runtime_app_id;bool runtime_started=false,gui_loaded=false,resources=false;};
 System& owner_;std::map<int,AppRecord> apps_;Scheduler* task_scheduler_;Runtime* runtime_;Policy package_policy_;int active_app_id_=0;uint64_t next_instance_=1;
 bool should_schedule_app_task(){return false;}
 template<class R,class F>R run_task_sync(int,F fn,R){return fn();}
 auto get_record(int id)->std::expected<AppRecord*,std::string>{auto it=apps_.find(id);if(it==apps_.end())return std::unexpected("missing");return &it->second;}
 using TransientOverlayRecord=int;
 std::expected<std::optional<int>,std::string> show_app_launch_transition(AppRecord&,const AppStartOptions&){return std::optional<int>{};}
 void hide_transient_overlay(std::optional<int>&){}
 bool advancing_app_starts_=false;
 void advance_app_starts(bool drain=false);
 Result prepare_app_start_gui(AppRecord& r){r.resources=true;r.gui_loaded=true;return failure=="gui"?Result(std::unexpected(failure)):Result{};}
 Result ensure_runtime_loaded(AppRecord& r){if(failure=="runtime_load")return std::unexpected(failure);r.runtime_app_id=9;return {};}
 Result call_runtime_lifecycle(AppRecord&,const char* name){return failure=="lifecycle" && std::string(name)=="on_start"?Result(std::unexpected(failure)):Result{};}
 void cleanup_app_transient_resources(AppRecord&){}
 void unload_runtime(AppRecord&r){r.runtime_started=false;r.runtime_app_id.reset();}
 void clear_pending_gui_bindings(int){}
 void unload_gui(AppRecord&r){if(failure=="cleanup"){failure.clear();throw std::runtime_error("cleanup");}r.gui_loaded=false;}
 void unregister_app_gui_resources(AppRecord&r){r.resources=false;}
 void execute_task_with_group_context(int group,std::function<void()> cb){assert(group==SYSTEM_GUI_TASK_GROUP);cb();}
 Result admit_app_start(AppRecord&);
 Result start_app_runtime(AppRecord&);
 Result call_app_start(AppRecord&);
 Result commit_app_start(AppRecord&);
 void release_app_start_runtime(AppRecord&);
 void rollback_app_start_gui(AppRecord&);
 void report_app_start_failure(AppRecord&,const std::string&,AppStartFailureKind=AppStartFailureKind::Lifecycle);
};
Result System::stop_app(AppId id){auto found=impl_->get_record(id);assert(found);auto &record=**found;
''' + cancel + r'''
return {};}
}
''' + 'namespace esp_brookesia::system::core {\n' + operations + synchronous + '}\n' + source + r'''
using namespace esp_brookesia::system::core;
struct Fixture {System s;Scheduler q;Runtime runtime;System::Impl impl;
 Fixture():s{&impl},impl{s,{},&q,&runtime}{impl.apps_[1].info.app_id=1;impl.apps_[2].info.app_id=2;}
 void tick(){impl.advance_app_starts();}
 void settle(){for(int i=0;i<25 && impl.apps_[1].pending_start;++i){q.run();tick();}assert(!impl.apps_[1].pending_start);}
};
int main(){
 // Compile both real entry paths: the same admission error must give the same actionable hint.
 failure="developer_mode_required";Fixture sync;assert(!sync.s.start_app(1));
 const auto expected_kind=dialog_kind,expected_detail=dialog_detail;
 assert(expected_kind=="admission" && expected_detail.find("Enable Developer Mode")!=std::string::npos);
 Fixture phased;assert(phased.s.request_app_start(1));phased.settle();
 assert(dialog_kind==expected_kind && dialog_detail==expected_detail);
 failure.clear();
 for(auto stage:{"admission","services","runtime_load","runtime_start","lifecycle"}) {
  failure=stage;Fixture synchronous;assert(!synchronous.s.start_app(1));
  assert(synchronous.s.failed==1 && synchronous.s.started==0);
  const auto kind=dialog_kind,detail=dialog_detail;
  Fixture asynchronous;assert(asynchronous.s.request_app_start(1));asynchronous.settle();
  assert(asynchronous.s.failed==1 && asynchronous.s.started==0);
  assert(dialog_kind==kind && dialog_detail==detail);
  assert(!synchronous.impl.apps_[1].runtime_app_id && !asynchronous.impl.apps_[1].runtime_app_id);
 }
 failure.clear();
 for(auto kind:{AppKind::Runtime,AppKind::Native}) {
  Fixture synchronous;synchronous.impl.apps_[1].info.manifest.kind=kind;
  assert(synchronous.s.start_app(1));assert(synchronous.s.started==1);
  Fixture asynchronous;asynchronous.impl.apps_[1].info.manifest.kind=kind;
  assert(asynchronous.s.request_app_start(1));asynchronous.settle();assert(asynchronous.s.started==1);
  assert(synchronous.impl.apps_[1].info.state==asynchronous.impl.apps_[1].info.state);
  assert(synchronous.impl.active_app_id_==asynchronous.impl.active_app_id_);
 }
 Fixture f;assert(f.s.request_app_start(1));auto identity=f.impl.apps_[1].pending_start;auto instance=f.impl.apps_[1].execution.instance;assert(instance!=0);
 assert(f.s.request_app_start(1));assert(f.impl.apps_[1].pending_start==identity && f.impl.apps_[1].execution.instance==instance);
 assert(!f.s.request_app_start(2));f.tick();f.tick();assert(f.q.queued.size()==1);
 // The real progress method polls, never waits for an unfinished GUI future.
 const auto before=std::chrono::steady_clock::now();for(int i=0;i<20;++i)f.tick();
 assert(std::chrono::steady_clock::now()-before<std::chrono::milliseconds(50));assert(f.s.started==0);
 assert(f.s.stop_app(1));assert(!f.s.request_app_start(1));f.tick();assert(f.impl.apps_[1].pending_start);
 f.settle();assert(f.s.started==0 && f.s.stopped==1 && !f.impl.apps_[1].gui_loaded && !f.impl.apps_[1].resources);
 assert(f.s.request_app_start(1));assert(f.impl.apps_[1].pending_start!=identity && f.impl.apps_[1].execution.instance!=instance);f.settle();assert(f.s.started==1 && f.impl.apps_[1].info.state==AppState::Running);
 for(auto stage:{"admission","services","gui","runtime_load","runtime_start","lifecycle","commit"}){
  failure=stage;Fixture failed;assert(failed.s.request_app_start(1));failed.settle();
  assert(failed.s.failed==1 && failed.impl.apps_[1].info.state==AppState::Error);
  assert(!failed.impl.apps_[1].gui_loaded && !failed.impl.apps_[1].resources && !failed.impl.apps_[1].runtime_app_id);
 }
 failure.clear();Fixture native;native.impl.apps_[1].info.manifest.kind=AppKind::Native;
 assert(native.s.request_app_start(1));native.settle();assert(native.impl.apps_[1].native_app->starts==1);
 Fixture rejected;assert(rejected.s.request_app_start(1));rejected.tick();rejected.q.allow=false;rejected.tick();
 assert(rejected.impl.apps_[1].pending_start);rejected.tick();assert(rejected.impl.apps_[1].pending_start);
 rejected.q.allow=true;rejected.settle();assert(rejected.s.failed==1);
 Fixture cleanup;assert(cleanup.s.request_app_start(1));cleanup.tick();cleanup.tick();cleanup.q.run();
 cleanup.tick();assert(cleanup.s.stop_app(1));failure="cleanup";cleanup.settle();assert(cleanup.s.stopped==1 && !cleanup.impl.apps_[1].resources);
 Fixture stop_failure;stop_failure.impl.apps_[1].info.manifest.kind=AppKind::Native;
 assert(stop_failure.s.request_app_start(1));
 for(int i=0;i<20 && stop_failure.impl.apps_[1].pending_start->phase!=System::Impl::PendingAppStart::Phase::Commit;++i){stop_failure.q.run();stop_failure.tick();}
 assert(stop_failure.s.stop_app(1));failure="stop";stop_failure.settle();failure.clear();
 assert(stop_failure.s.failed==1 && stop_failure.s.stopped==0 && stop_failure.impl.apps_[1].native_app->stops==1);
 Fixture both;both.impl.apps_[1].info.manifest.kind=AppKind::Native;
 failure="both";assert(both.s.request_app_start(1));both.settle();failure.clear();
 assert(both.impl.apps_[1].info.last_error=="stop-error" && dialog_detail=="start-error");
 Fixture drain;assert(drain.s.request_app_start(1));drain.impl.advance_app_starts(true);assert(drain.s.stopped==1 && !drain.impl.apps_[1].pending_start);
}
'''
            (root/'test.cpp').write_text(harness)
            binary=root/'test'
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23','-pthread',str(root/'test.cpp'),'-o',str(binary)],check=True)
            subprocess.run([str(binary)],check=True,timeout=10)


if __name__ == '__main__':
    unittest.main()
