"""Execute actual locked Core lifecycle bodies with fault-injected dependencies."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
COMPONENTS = ROOT / 'firmware/managed_components'
HARNESS = r'''
#include <atomic>
#include <cassert>
#include <chrono>
#include <expected>
#include <filesystem>
#include <functional>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>
#include "brookesia/lib_utils/function_guard.hpp"
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS(...)
#define BROOKESIA_LOGI(...)
#define BROOKESIA_LOGD(...)
#define BROOKESIA_LOGW(...)
#define BROOKESIA_LOGE(...)
#define BROOKESIA_SYSTEM_CORE_DEFAULT_SYSTEM_TYPE "host"
#define BROOKESIA_SYSTEM_CORE_WORKER_POLL_INTERVAL_MS 1
#define BROOKESIA_SYSTEM_CORE_TIMER_SERVICE_NAME "timer"
#define BROOKESIA_SYSTEM_CORE_GUI_SERVICE_NAME "gui"
#define BROOKESIA_SYSTEM_CORE_SERVICE_NAME "system"
using Result = std::expected<void, std::string>;
std::string failure;
bool throw_failure = false, reject_cleanup = false, fonts_alive = true, adapter_alive = true;
unsigned backends = 0, hooks = 0, scheduler_stops = 0, gui_pops = 0, gui_unloads = 0;
thread_local unsigned adapter_depth = 0;
std::recursive_mutex adapter_mutex;
void adapter_lock() { assert(adapter_alive); adapter_mutex.lock(); ++adapter_depth; }
void adapter_unlock() { assert(adapter_depth); --adapter_depth; adapter_mutex.unlock(); }
bool pass(const std::string &stage) {
    if (stage != failure) return true;
    if (throw_failure) throw std::runtime_error(stage);
    return false;
}
Result checked(const std::string &stage) { if (!pass(stage)) return std::unexpected(stage); return {}; }
namespace boost::this_thread {
void sleep_for(const boost::chrono::milliseconds &duration) {
    std::this_thread::sleep_for(std::chrono::milliseconds(duration.count()));
}
}
namespace esp_brookesia {
namespace lib_utils {
struct ThreadConfig {};
struct TaskScheduler {
    struct StartConfig { std::vector<ThreadConfig> worker_configs; int worker_poll_interval_ms; };
    bool running = false, worker = false;
    std::function<void()> pending_callback;
    bool start(const StartConfig &) { running = pass("scheduler"); return running; }
    bool is_running() const { return running; }
    bool is_current_thread_worker() const { return worker; }
    void cancel(int) {}
    void stop() {
        assert(!worker && adapter_depth == 0);
        if (running && pending_callback) {
            std::thread pending(pending_callback);
            pending.join();
        }
        running = false;
        ++scheduler_stops;
    }
};
}
namespace gui {
struct ThreadGuard { std::function<void()> lock, unlock; };
struct Backend {
    Backend() { ++backends; }
    ~Backend() { adapter_lock(); assert(fonts_alive); --backends; adapter_unlock(); }
    std::optional<ThreadGuard> get_thread_guard() { return ThreadGuard{adapter_lock, adapter_unlock}; }
};
struct RuntimeTaskConfig {
    std::shared_ptr<lib_utils::TaskScheduler> task_scheduler;
    std::string gui_group, event_group;
    bool enable_fast_action_dispatch;
};
struct Runtime {
    std::unique_ptr<Backend> backend;
    Runtime(std::unique_ptr<Backend> input, RuntimeTaskConfig) : backend(std::move(input)) {
        if (!pass("gui_construct")) throw std::runtime_error("gui_construct");
    }
    ~Runtime() { assert(adapter_depth && fonts_alive && adapter_alive); }
    void set_view_debug_enabled(bool) {}
    void process_backend() {}
    bool pop_transient_screen(int) { adapter_lock(); ++gui_pops; adapter_unlock(); return true; }
    bool unload(int) { adapter_lock(); ++gui_unloads; adapter_unlock(); return true; }
};
}
namespace runtime {
using AppId = int;
struct RuntimeFunctionBridge {};
struct Runtime {
    template<class Bridge> explicit Runtime(Bridge) {}
    void deinit() {}
};
}
namespace service {
struct ServiceBase { std::string name; explicit ServiceBase(std::string value) : name(std::move(value)) {} };
struct ServiceBinding { bool valid = false; bool is_valid() const { return valid; } void release() { valid = false; } };
struct ServiceManager {
    bool initialized = false;
    std::map<std::string, std::shared_ptr<ServiceBase>> services;
    static ServiceManager &get_instance() { static ServiceManager manager; return manager; }
    bool is_initialized() const { return initialized; }
    bool init() { initialized = pass("manager_init"); return initialized; }
    bool start() { return pass("manager_start"); }
    bool add_service(const std::shared_ptr<ServiceBase> &value) {
        if (!pass("add_" + value->name)) return false;
        services.emplace(value->name, value);
        return true;
    }
    ServiceBinding bind(const std::string &name) { return {pass("bind_" + name)}; }
    bool remove_service(const std::string &name) { services.erase(name); return true; }
    std::shared_ptr<ServiceBase> get_service(const std::string &name) {
        auto found = services.find(name);
        return found == services.end() ? nullptr : found->second;
    }
};
}
namespace system::core {
using AppId = int;
constexpr int INVALID_APP_ID = 0;
constexpr const char *SYSTEM_GUI_TASK_GROUP = "gui", *SYSTEM_GUI_INPUT_TASK_GROUP = "gui_input";
constexpr const char *SYSTEM_APP_INPUT_TASK_GROUP = "input";
std::vector<lib_utils::ThreadConfig> make_scheduler_worker_configs() { return {}; }
struct StorageFileLocation {};
struct RuntimePackagePolicy { bool reuse_verified_installations = true; };
Result initialize_runtime_package_validation(const RuntimePackagePolicy &, const std::vector<std::string> &) {
    return checked("package_validation");
}
struct SystemHostBridge {
    template<class... Arguments> explicit SystemHostBridge(Arguments&&...) {
        if (!pass("host_bridge")) throw std::runtime_error("host_bridge");
    }
    std::shared_ptr<runtime::RuntimeFunctionBridge> get_function_bridge() { return {}; }
};
struct SystemService : service::ServiceBase { template<class Owner> explicit SystemService(Owner &) : ServiceBase("system") {} };
struct GuiService : service::ServiceBase { template<class Owner> explicit GuiService(Owner &) : ServiceBase("gui") {} };
struct TimerService : service::ServiceBase { template<class Owner> explicit TimerService(Owner &) : ServiceBase("timer") {} };
enum class AppState { Installed, Running, Paused };
struct NativeApp { void on_uninstall(int &) {} };
struct System {
    struct Config {
        std::string system_type;
        struct Environment { std::string theme_id, language; } environment;
        RuntimePackagePolicy package_policy;
        std::unique_ptr<gui::Backend> gui_backend;
        bool enable_gui_view_debug = false, start_service_manager = true;
        bool install_registered_apps = true, install_package_apps = true;
        struct Overlay { int min_present_ms = 0; } startup_overlay;
    };
    struct Impl {
        struct AppRecord {
            struct Info { AppState state = AppState::Installed; int app_id = 1; } info;
            std::shared_ptr<NativeApp> native_app;
            std::unique_ptr<int> context;
        };
        struct TransientOverlayRecord {
            int document_id = 1, mount_id = 2;
            std::chrono::steady_clock::time_point shown_at = std::chrono::steady_clock::now();
        };
        std::string system_type_;
        Config::Environment environment_;
        RuntimePackagePolicy package_policy_;
        Config config_;
        bool initialized_ = false, started_ = false, runtime_initialized_ = false;
        bool initializing_ = false, product_init_entered_ = false;
        bool system_service_added_ = false, gui_service_added_ = false, timer_service_added_ = false;
        bool gui_preferences_restoring_ = false, gui_preferences_restored_ = false;
        int active_app_id_ = 0;
        std::map<int, int> keyboard_requests_, message_dialog_requests_, pending_gui_bindings_, app_storage_paths_cache_;
        std::vector<int> queued_message_dialog_requests_, pending_timers_;
        std::optional<int> active_message_dialog_request_id_;
        std::shared_ptr<lib_utils::TaskScheduler> task_scheduler_;
        std::optional<gui::ThreadGuard> gui_thread_guard_;
        std::unique_ptr<gui::Runtime> gui_runtime_;
        std::unique_ptr<runtime::Runtime> runtime_;
        std::shared_ptr<SystemHostBridge> host_bridge_;
        std::shared_ptr<runtime::RuntimeFunctionBridge> runtime_function_bridge_;
        std::shared_ptr<SystemService> system_service_;
        std::shared_ptr<GuiService> gui_service_;
        std::shared_ptr<TimerService> timer_service_;
        service::ServiceBinding system_service_binding_, gui_service_binding_, timer_service_binding_;
        std::map<int, AppRecord> apps_;
        std::map<int, int> runtime_to_app_, manifest_id_to_app_, image_resource_owners_, font_resource_owners_;
        std::optional<TransientOverlayRecord> startup_overlay_;
        std::optional<int> live_preview_poll_task_id_;
        std::set<int> live_preview_document_ids_;
        void set_gui_theme_snapshot(const std::string &) { if (!pass("snapshot")) throw std::runtime_error("snapshot"); }
        void set_gui_language_snapshot(const std::string &) {}
        bool configure_task_groups() {
            task_scheduler_->pending_callback = [this, guard_required = gui_thread_guard_.has_value()] {
                if (!guard_required) return;
                assert(gui_thread_guard_);
                gui_thread_guard_->lock();
                gui_thread_guard_->unlock();
            };
            return pass("groups");
        }
        template<class Output, class Callback> Output run_task_sync(const char *, Callback callback, Output fallback) {
            if (reject_cleanup && task_scheduler_ && task_scheduler_->is_running()) return fallback;
            bool guarded = gui_thread_guard_.has_value() && task_scheduler_ && task_scheduler_->is_running();
            if (guarded) gui_thread_guard_->lock();
            lib_utils::FunctionGuard unlock([this, guarded] { if (guarded) gui_thread_guard_->unlock(); });
            return callback();
        }
        Result post_gui_task(std::function<void()> callback) {
            return run_task_sync<Result>(SYSTEM_GUI_TASK_GROUP, [&] { callback(); return Result{}; }, std::unexpected("post"));
        }
        Result post_task(const char *, std::function<void()>) { return {}; }
        Result dispatch_event(int, std::string, std::string, std::string) { return {}; }
        std::expected<std::string, std::string> resolve_storage_file_path(int, const StorageFileLocation &) { return "host"; }
        Result initialize_storage_layout() { return checked("storage"); }
        std::vector<std::filesystem::path> get_app_scan_roots() { return {"host"}; }
        void load_gui_preferences() { if (!pass("preferences")) throw std::runtime_error("preferences"); }
        Result show_startup_overlay() {
            if (!pass("overlay")) return std::unexpected("overlay");
            if (gui_runtime_) startup_overlay_.emplace();
            return {};
        }
        Result install_unpacked_apps() { return checked("unpacked"); }
        void hide_startup_overlay();
        void stop_live_preview_poll();
        void cancel_app_timers(AppRecord &) {}
        void unload_runtime(AppRecord &) {}
        void clear_pending_gui_bindings(int) {}
        void clear_pending_gui_image_sources(int) {}
        void clear_all_pending_gui_image_sources() {}
        void unload_gui(AppRecord &) {}
        void unregister_app_gui_resources(AppRecord &) {}
        void unregister_app_icon_resource(AppRecord &) {}
    };
    std::unique_ptr<Impl> impl_ = std::make_unique<Impl>();
    virtual ~System() { deinit(); }
    Result init(Config);
    void stop();
    void deinit();
    void on_stop() {}
    Result stop_app(int) { return {}; }
    Result on_prepare_startup_overlay() { return checked("prepare_overlay"); }
    Result on_init() {
        impl_->apps_.try_emplace(1);
        return checked("product_init");
    }
    Result install_registered_apps() { return checked("registered"); }
    void on_deinit() {
        assert(!backends && !impl_->gui_runtime_ && !impl_->task_scheduler_ && !impl_->gui_thread_guard_);
        assert(adapter_alive && fonts_alive && adapter_depth == 0);
        fonts_alive = false;
        adapter_alive = false;
        ++hooks;
    }
};
'''
MAIN = r'''
}
}
using esp_brookesia::system::core::System;
using esp_brookesia::service::ServiceManager;
void reset_case() {
    assert(!backends && adapter_depth == 0);
    failure.clear(); throw_failure = false; reject_cleanup = false;
    fonts_alive = true; adapter_alive = true; hooks = 0; scheduler_stops = 0;
    auto &manager = ServiceManager::get_instance();
    manager.initialized = false; manager.services.clear();
}
System::Config configuration(bool backend = true) {
    System::Config config;
    if (backend) config.gui_backend = std::make_unique<esp_brookesia::gui::Backend>();
    return config;
}
void verify_clean(System &system, bool hook = true) {
    assert(!system.impl_->gui_runtime_ && !system.impl_->task_scheduler_ && !system.impl_->initialized_);
    assert(!system.impl_->startup_overlay_ && !system.impl_->gui_thread_guard_);
    assert(system.impl_->apps_.empty() && ServiceManager::get_instance().services.empty());
    assert(!backends && adapter_depth == 0 && hooks == unsigned(hook));
    system.deinit();
    assert(hooks == unsigned(hook));
}
int main(int argc, char **argv) {
    assert(argc == 2);
    const std::string mode = argv[1];
    if (mode == "failures") {
        for (const auto &stage : {"scheduler", "groups", "gui_construct", "host_bridge", "manager_init",
             "add_system", "add_gui", "add_timer", "manager_start", "bind_system", "bind_gui",
             "bind_timer", "storage", "package_validation", "prepare_overlay", "overlay",
             "product_init", "registered", "unpacked"}) {
            for (const bool throws : {false, true}) {
                reset_case(); failure = stage; throw_failure = throws;
                System system;
                bool failed = false;
                try {
                    auto result = system.init(configuration());
                    failed = !result;
                    if (!result) assert(!result.error().empty());
                }
                catch (const std::runtime_error &error) { assert(error.what() == failure); failed = true; }
                assert(failed);
                verify_clean(system, stage == std::string("product_init") ||
                                     stage == std::string("registered") || stage == std::string("unpacked"));
            }
        }
        for (const auto &stage : {"snapshot", "preferences"}) {
            reset_case(); failure = stage; throw_failure = true;
            System system;
            try { (void)system.init(configuration()); assert(false); }
            catch (const std::runtime_error &error) { assert(error.what() == failure); }
            verify_clean(system, false);
        }
    } else if (mode == "rejection") {
        for (unsigned partial = 0; partial < 3; ++partial) {
            reset_case();
            System system;
            assert(system.init(configuration()));
            if (partial) system.impl_->initialized_ = false;
            if (partial == 2) {
                system.impl_->task_scheduler_->stop();
                system.impl_->task_scheduler_.reset();
            }
            system.impl_->live_preview_poll_task_id_ = 7;
            system.impl_->live_preview_document_ids_.insert(1);
            reject_cleanup = true;
            system.deinit();
            verify_clean(system);
            assert(system.impl_->live_preview_document_ids_.empty());
        }
    } else if (mode == "success") {
        for (unsigned cycle = 0; cycle < 20; ++cycle) {
            reset_case();
            System system;
            assert(system.init(configuration()));
            auto *original = system.impl_->gui_runtime_.get();
            assert(system.init(configuration()));
            assert(system.impl_->gui_runtime_.get() == original && hooks == 0 && backends == 1);
            system.deinit(); verify_clean(system);
            fonts_alive = true; adapter_alive = true; hooks = 0;
            assert(system.init(configuration()));
            system.deinit(); verify_clean(system);
        }
        reset_case();
        System system;
        assert(system.init(configuration(false)));
        system.deinit(); verify_clean(system);
    } else if (mode == "worker") {
        reset_case();
        System system;
        assert(system.init(configuration()));
        system.impl_->task_scheduler_->worker = true;
        system.deinit();
        assert(system.impl_->initialized_ && system.impl_->gui_runtime_ && hooks == 0 && !scheduler_stops);
        system.impl_->initialized_ = false;
        auto refused = system.init(configuration(false));
        assert(!refused && !scheduler_stops && hooks == 0);
        system.impl_->task_scheduler_->worker = false;
        system.deinit(); verify_clean(system);
    } else if (mode == "foreign") {
        reset_case();
        auto foreign = std::make_shared<esp_brookesia::service::ServiceBase>("gui");
        ServiceManager::get_instance().services.emplace("gui", foreign);
        failure = "storage";
        System system;
        assert(!system.init(configuration()));
        assert(ServiceManager::get_instance().get_service("gui") == foreign);
        ServiceManager::get_instance().services.clear();
        verify_clean(system, false);
    } else return 3;
}
'''


def lifecycle_bodies(component):
    text = (component / 'src/system/lifecycle.cpp').read_text()
    signatures = [
        ('std::expected<void, std::string> System::init(Config config)',
         'std::expected<void, std::string> System::start()'),
        ('void System::stop()', 'void System::process_timers()'),
    ]
    result = ''.join(text[text.index(start):text.index(end)] for start, end in signatures)
    overlay = (component / 'src/system/overlay.cpp').read_text()
    start = overlay.index('void System::Impl::hide_startup_overlay()')
    result += overlay[start:overlay.index('\nstd::expected<', start)]
    gui = (component / 'src/system/gui.cpp').read_text()
    result += gui[gui.index('void System::Impl::stop_live_preview_poll()'):
                  gui.index('void System::Impl::stop_live_preview_poll_if_idle()')]
    return result


class CorePartialGuiInitializationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='espocket-core-lifecycle-')
        directory = Path(cls.temporary.name)
        override = os.environ.get('ESPOCKET_CORE_LIFECYCLE_COMPONENT')
        if override:
            component = Path(override)
        else:
            sys.path.insert(0, str(ROOT / 'scripts/firmware'))
            from prepare_patched_component import prepare
            component = prepare(COMPONENTS / 'espressif__brookesia_system_core',
                                ROOT / 'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json',
                                directory / 'component')
        source = directory / 'probe.cpp'
        source.write_text(HARNESS + lifecycle_bodies(component) + MAIN)
        cls.binary = directory / 'probe'
        subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-O2', '-pthread',
                        '-DBOOST_NO_USER_CONFIG',
                        '-I' + str(COMPONENTS / 'espressif__brookesia_lib_utils/include'),
                        '-I' + str(COMPONENTS / 'espressif__esp-boost/src'),
                        str(source), '-o', str(cls.binary)], check=True, timeout=90)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def exercise(self, mode):
        result = subprocess.run([str(self.binary), mode], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_failure_returns_and_exceptions_release_borrowers(self):
        self.exercise('failures')

    def test_rejected_cleanup_joins_workers_before_locked_gui_destruction(self):
        self.exercise('rejection')

    def test_success_repeated_init_deinit_and_no_backend(self):
        self.exercise('success')

    def test_worker_lifecycle_calls_do_not_self_join(self):
        self.exercise('worker')

    def test_rollback_preserves_foreign_service_registration(self):
        self.exercise('foreign')


if __name__ == '__main__':
    unittest.main()
