"""Execute full hash-patched Core init/deinit methods with acquisition failures.

Fake scheduler and GUI model ownership and rejected posts, not device threading.
"""
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/firmware'))
from prepare_patched_component import prepare

STUB=r'''
#include <cassert>
#include <atomic>
#include <expected>
#include <functional>
#include <map>
#include <memory>
#include <optional>
#include <string>
#include <vector>
#include <string_view>
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS(...) ((void)0)
#define BROOKESIA_LOGI(...) ((void)0)
#define BROOKESIA_LOGD(...) ((void)0)
#define BROOKESIA_LOGW(...) ((void)0)
#define BROOKESIA_SYSTEM_CORE_VER_MAJOR 0
#define BROOKESIA_SYSTEM_CORE_VER_MINOR 8
#define BROOKESIA_SYSTEM_CORE_VER_PATCH 4
constexpr auto BROOKESIA_SYSTEM_CORE_DEFAULT_SYSTEM_TYPE="test";
constexpr auto BROOKESIA_SYSTEM_CORE_SERVICE_NAME="SystemCore";
constexpr auto BROOKESIA_SYSTEM_CORE_GUI_SERVICE_NAME="SystemGui";
constexpr auto BROOKESIA_SYSTEM_CORE_TIMER_SERVICE_NAME="SystemTimer";
constexpr int BROOKESIA_SYSTEM_CORE_WORKER_POLL_INTERVAL_MS=1;
constexpr auto SYSTEM_GUI_TASK_GROUP="gui",SYSTEM_GUI_INPUT_TASK_GROUP="gui-input",SYSTEM_APP_INPUT_TASK_GROUP="input";
int fail=0,stage=0,schedulers=0,guis=0,runtimes=0,product_inits=0,product_deinits=0;bool reject_gui=false;
bool injected(){return ++stage==fail;}
namespace lib_utils {
struct ThreadConfig{};
struct TaskScheduler {struct StartConfig{std::vector<ThreadConfig> worker_configs;int worker_poll_interval_ms;};bool running=false;
bool start(StartConfig){if(injected())return false;running=true;++schedulers;return true;}
void stop(){if(running){--schedulers;running=false;}}bool is_running(){return running;}};
struct FunctionGuard {std::function<void()> fn;FunctionGuard(std::function<void()> f):fn(f){}~FunctionGuard(){if(fn)fn();}void release(){fn={};}};
}
namespace gui {
struct Environment {std::string theme_id="dark",language="en";};
struct Backend {struct Guard{std::function<void()> lock,unlock;};std::optional<Guard> get_thread_guard(){return {};}};
struct RuntimeTaskConfig {std::shared_ptr<lib_utils::TaskScheduler> task_scheduler;std::string gui_group,event_group;bool enable_fast_action_dispatch;};
struct Runtime {Runtime(auto&&,auto&&){++guis;}~Runtime(){--guis;}void set_view_debug_enabled(bool){}};
}
namespace runtime {using AppId=int;struct RuntimeFunctionBridge{};struct Runtime {Runtime(auto){++runtimes;}~Runtime(){--runtimes;}void deinit(){}};}
struct StorageFileLocation{};
struct SystemHostBridge {template<class... T>SystemHostBridge(T&&...){}auto get_function_bridge(){return std::make_shared<runtime::RuntimeFunctionBridge>();}};
struct SystemService{SystemService(auto&) {}};struct GuiService{GuiService(auto&) {}};struct TimerService{TimerService(auto&) {}};
namespace service {
struct Binding {bool valid=false;bool is_valid(){return valid;}void release(){valid=false;}};
struct ServiceManager {bool initialized=false;std::vector<std::string> names;
static ServiceManager& get_instance(){static ServiceManager m;return m;}
bool is_initialized(){return initialized;}bool init(){if(injected())return false;initialized=true;return true;}
bool add_service(auto ptr){if(injected())return false;std::string name;
using T=typename decltype(ptr)::element_type;if constexpr(std::is_same_v<T,SystemService>)name="SystemCore";else if constexpr(std::is_same_v<T,GuiService>)name="SystemGui";else name="SystemTimer";
names.push_back(name);return true;}
bool start(){return !injected();}Binding bind(auto){return {!injected()};}
void remove_service(std::string name){auto it=std::find(names.begin(),names.end(),name);assert(it!=names.end());names.erase(it);}};
}
namespace esp_brookesia::system::core {
struct PackagePolicy {bool reuse_verified_installations=false;};
std::expected<void,std::string> initialize_runtime_package_validation(auto&,auto&){return {};}
using AppId=int;constexpr int INVALID_APP_ID=0;enum class AppState{Installed,Running,Paused};
struct Native{void on_uninstall(auto&) {}};
struct Record{struct{AppState state=AppState::Installed;int app_id=1;}info;std::shared_ptr<Native> native_app;std::shared_ptr<int> context;};
struct System {
struct Config {PackagePolicy package_policy;std::string system_type="test";gui::Environment environment;std::unique_ptr<gui::Backend> gui_backend=std::make_unique<gui::Backend>();bool enable_gui_view_debug=false,start_service_manager=true,install_registered_apps=true,install_package_apps=true;};
struct Impl {
#ifdef PATCHED_FIELDS
bool initializing_=false,product_init_entered_=false,system_service_added_=false,gui_service_added_=false,timer_service_added_=false;
#endif
bool initialized_=false,started_=false,runtime_initialized_=false,gui_preferences_restoring_=false,gui_preferences_restored_=false;
PackagePolicy package_policy_;std::string system_type_;gui::Environment environment_;Config config_;
std::shared_ptr<lib_utils::TaskScheduler> task_scheduler_;
std::unique_ptr<gui::Runtime> gui_runtime_;std::optional<gui::Backend::Guard> gui_thread_guard_;
std::shared_ptr<SystemHostBridge> host_bridge_;std::shared_ptr<runtime::RuntimeFunctionBridge> runtime_function_bridge_;std::unique_ptr<runtime::Runtime> runtime_;
std::shared_ptr<SystemService> system_service_;std::shared_ptr<GuiService> gui_service_;std::shared_ptr<TimerService> timer_service_;
service::Binding system_service_binding_,gui_service_binding_,timer_service_binding_;
std::map<int,Record> apps_;std::map<int,int> runtime_to_app_,manifest_id_to_app_,image_resource_owners_,font_resource_owners_,keyboard_requests_,message_dialog_requests_,pending_gui_bindings_,app_storage_paths_cache_;
std::vector<int> queued_message_dialog_requests_,pending_timers_;std::optional<int> active_message_dialog_request_id_;int active_app_id_=0;
void set_gui_theme_snapshot(auto){}void set_gui_language_snapshot(auto){}bool configure_task_groups(){return !injected();}
std::expected<std::string,std::string> resolve_storage_file_path(int,const StorageFileLocation&){return "path";}
std::expected<void,std::string> dispatch_event(auto...){return {};}
std::expected<void,std::string> post_task(auto,auto){return {};}
std::expected<void,std::string> initialize_storage_layout(){if(injected())return std::unexpected("storage");return {};}
struct Root {std::string generic_string() const{return "root";}};std::vector<Root> get_app_scan_roots(){return {};}
void load_gui_preferences(){}std::expected<void,std::string> show_startup_overlay(){if(injected())return std::unexpected("overlay");return {};}
void hide_startup_overlay(){}std::expected<void,std::string> install_unpacked_apps(){if(injected())return std::unexpected("packages");return {};}
void cancel_app_timers(auto&){}void unload_runtime(auto&){}void clear_pending_gui_bindings(int){}void clear_pending_gui_image_sources(int){}void clear_all_pending_gui_image_sources(){}void unload_gui(auto&){}void unregister_app_gui_resources(auto&){}void unregister_app_icon_resource(auto&){}void stop_live_preview_poll(){}
template<class R,class F>R run_task_sync(auto,F f,R rejected){if(reject_gui && task_scheduler_ && task_scheduler_->running)return rejected;return f();}
void execute_task_with_group_context(auto,auto f){assert(!task_scheduler_);f();}
};
std::unique_ptr<Impl> impl_=std::make_unique<Impl>();
std::expected<void,std::string> init(Config);void deinit();std::expected<void,std::string> start();void stop();
std::expected<void,std::string> on_start(){return {};}void on_stop(){}std::expected<void,std::string> stop_app(int){return {};}
std::expected<void,std::string> on_prepare_startup_overlay(){if(injected())return std::unexpected("prepare");return {};}
std::expected<void,std::string> on_init(){++product_inits;if(injected())return std::unexpected("product");return {};}
std::expected<void,std::string> install_registered_apps(){if(injected())return std::unexpected("registered");return {};}
void on_deinit(){++product_deinits;}
};
namespace {std::vector<lib_utils::ThreadConfig> make_scheduler_worker_configs(){return {};}}
'''

class CoreInitializationCleanupTest(unittest.TestCase):
    def exercise(self,core):
        text=(core/'src/system/lifecycle.cpp').read_text()
        init=text[text.index('std::expected<void, std::string> System::init(Config config)'):text.index('std::expected<void, std::string> System::start()')]
        deinit=text[text.index('void System::deinit()'):text.index('void System::process_timers()')]
        running=text[text.index('std::expected<void, std::string> System::start()'):text.index('void System::deinit()')]
        fields='#define PATCHED_FIELDS\n' if 'initializing_' in text else ''
        harness=fields+STUB+init+running+deinit+r'''
}
int main(){using esp_brookesia::system::core::System;
for(int point=1;point<=16;++point){stage=0;fail=point;product_inits=product_deinits=0;service::ServiceManager::get_instance()={};
System s;auto result=s.init(System::Config{});assert(!result);s.deinit();
assert(schedulers==0 && guis==0 && runtimes==0);assert(service::ServiceManager::get_instance().names.empty());assert(product_inits==product_deinits);assert(!s.impl_->initialized_);}
reject_gui=false;fail=0;stage=0;service::ServiceManager::get_instance()={};System repeated;
for(int round=0;round<3;++round){assert(repeated.init(System::Config{}));assert(repeated.start());repeated.stop();assert(!repeated.impl_->started_ && repeated.impl_->initialized_);assert(repeated.start());repeated.deinit();assert(schedulers==0 && guis==0 && runtimes==0);assert(!repeated.impl_->initialized_);}
for(bool reject:{false,true}){reject_gui=reject;fail=0;stage=0;service::ServiceManager::get_instance()={};System s;assert(s.init(System::Config{}));s.deinit();assert(schedulers==0 && guis==0 && runtimes==0);s.deinit();}
}
'''
        with tempfile.TemporaryDirectory(prefix='core-init-seam-') as directory:
            cpp=Path(directory)/'test.cpp';binary=Path(directory)/'test';cpp.write_text(harness)
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23',str(cpp),'-o',str(binary)],check=True)
            return subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)
    def test_partial_init_and_rejected_gui_teardown(self):
        core=ROOT/'firmware/managed_components/espressif__brookesia_system_core'
        with tempfile.TemporaryDirectory(prefix='core-init-patched-') as directory:
            patched=prepare(core,ROOT/'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json',Path(directory)/'core')
            baseline=self.exercise(core);self.assertNotEqual(baseline.returncode,0,baseline.stderr)
            result=self.exercise(patched);self.assertEqual(result.returncode,0,result.stderr)
