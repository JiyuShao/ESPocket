#include "espocket/system.hpp"

#include <algorithm>
#include <cinttypes>
#include <utility>
#include <vector>

#include "sdkconfig.h"

#include "boost/json/array.hpp"
#include "boost/json/value.hpp"
#include "brookesia/app_settings.hpp"
#include "brookesia/app_store.hpp"
#include "brookesia/gui_lvgl.hpp"
#include "brookesia/lib_utils/describe_helpers.hpp"
#if CONFIG_ESPOCKET_M2_LIFECYCLE_STRESS
#include "brookesia/lib_utils/memory_profiler.hpp"
#endif
#include "brookesia/service_helper/media/display.hpp"
#include "brookesia/service_manager/helper/base.hpp"
#if CONFIG_ESPOCKET_M6_RESOURCE_TRACE
#include "esp_heap_caps.h"
#endif
#include "esp_log.h"
#include "esp_timer.h"
#include "espocket/circular_shell.hpp"
#include "espocket/hello_app.hpp"
#include "espocket/page_navigator.hpp"
#include "espocket/power_key_monitor.hpp"

namespace espocket {
namespace {

constexpr char TAG[] = "ESPocket.System";
constexpr uint32_t DISPLAY_TIMEOUT_MS = 1000;

using DisplayHelper = esp_brookesia::service::helper::Display;
using DisplaySource = esp_brookesia::gui::lvgl::DisplaySource;

#if CONFIG_ESPOCKET_M2_LIFECYCLE_STRESS
constexpr size_t M2_STRESS_CYCLES = 50;

std::expected<void, std::string> run_m2_lifecycle_stress(
    esp_brookesia::system::core::System &system,
    esp_brookesia::system::core::AppId app_id
)
{
    using AppState = esp_brookesia::system::core::AppState;
    using MemoryProfiler = esp_brookesia::lib_utils::MemoryProfiler;

    ESP_LOGI(TAG, "M2_STRESS BEGIN cycles=%zu app_id=%" PRIu32, M2_STRESS_CYCLES, app_id);
    for (size_t cycle = 1; cycle <= M2_STRESS_CYCLES; ++cycle) {
        const auto expected_state = cycle == 1 ? AppState::Installed : AppState::Stopped;
        auto before_start = system.get_app(app_id);
        if (!before_start.has_value() || before_start->state != expected_state) {
            ESP_LOGE(TAG, "M2_STRESS FAIL cycle=%zu phase=pre_start_state", cycle);
            return std::unexpected("M2 lifecycle stress has an invalid pre-start state at cycle " + std::to_string(cycle));
        }

        auto start_result = system.start_app(app_id);
        if (!start_result) {
            ESP_LOGE(TAG, "M2_STRESS FAIL cycle=%zu phase=start error=%s", cycle, start_result.error().c_str());
            return std::unexpected("M2 lifecycle stress start failed at cycle " + std::to_string(cycle));
        }

        auto running = system.get_app(app_id);
        if (!running.has_value() || running->state != AppState::Running) {
            ESP_LOGE(TAG, "M2_STRESS FAIL cycle=%zu phase=running_state", cycle);
            auto cleanup_result = system.stop_app(app_id);
            if (!cleanup_result) {
                ESP_LOGE(TAG, "M2_STRESS cleanup failed: %s", cleanup_result.error().c_str());
            }
            return std::unexpected("M2 lifecycle stress did not reach Running at cycle " + std::to_string(cycle));
        }

        auto stop_result = system.stop_app(app_id);
        if (!stop_result) {
            ESP_LOGE(TAG, "M2_STRESS FAIL cycle=%zu phase=stop error=%s", cycle, stop_result.error().c_str());
            return std::unexpected("M2 lifecycle stress stop failed at cycle " + std::to_string(cycle));
        }

        auto stopped = system.get_app(app_id);
        if (!stopped.has_value() || stopped->state != AppState::Stopped) {
            ESP_LOGE(TAG, "M2_STRESS FAIL cycle=%zu phase=stopped_state", cycle);
            return std::unexpected("M2 lifecycle stress did not reach Stopped at cycle " + std::to_string(cycle));
        }

        auto gui_probe = system.gui_set_text(app_id, "/hello/counter", "cleanup probe");
        if (gui_probe || gui_probe.error() != "App GUI document is not loaded") {
            ESP_LOGE(TAG, "M2_STRESS FAIL cycle=%zu phase=gui_cleanup", cycle);
            return std::unexpected("M2 lifecycle stress GUI cleanup failed at cycle " + std::to_string(cycle));
        }

        const auto heap = MemoryProfiler::take_raw_heap_snapshot();
        if (!heap.valid || heap.internal_free == 0 || heap.external_free == 0 ||
                heap.internal_largest == 0 || heap.external_largest == 0) {
            ESP_LOGE(TAG, "M2_STRESS FAIL cycle=%zu phase=heap_snapshot", cycle);
            return std::unexpected("M2 lifecycle stress heap snapshot failed at cycle " + std::to_string(cycle));
        }

        ESP_LOGI(
            TAG,
            "M2_STRESS CYCLE cycle=%zu start=Running stop=Stopped gui=Unloaded internal_free=%zu psram_free=%zu "
            "internal_largest=%zu psram_largest=%zu",
            cycle,
            heap.internal_free,
            heap.external_free,
            heap.internal_largest,
            heap.external_largest
        );
    }

    ESP_LOGI(TAG, "M2_STRESS COMPLETE cycles=%zu", M2_STRESS_CYCLES);
    return {};
}
#endif

} // namespace

System::System()
    : launch_source_(ShellSurface::WatchFace),
      lifecycle_restore_surface_(ShellSurface::WatchFace)
{}

System::~System() = default;

std::expected<void, std::string> System::init()
{
    auto &service_manager = esp_brookesia::service::ServiceManager::get_instance();
    if (!service_manager.init()) {
        return std::unexpected("Failed to initialize ServiceManager");
    }
    if (!service_manager.start()) {
        return std::unexpected("Failed to start ServiceManager");
    }

    auto display_result = start_display();
    if (!display_result) {
        return display_result;
    }

    esp_brookesia::system::core::System::Config config;
    config.gui_backend = std::make_unique<esp_brookesia::gui::lvgl::Backend>();
    config.environment = {
        .width_px = static_cast<int32_t>(display_width_),
        .height_px = static_cast<int32_t>(display_height_),
        .density = 1.0F,
        .font_scale = 1.0F,
        .language = "en",
        .theme_id = "dark",
    };
    config.system_type = "espocket";
    config.start_service_manager = true;
    config.install_registered_apps = false;
    config.install_package_apps = true;

    auto result = esp_brookesia::system::core::System::init(std::move(config));
    if (!result) {
        DisplaySource::get_instance().stop();
        display_binding_.release();
        display_started_ = false;
        return result;
    }
    return {};
}

esp_brookesia::system::core::SystemInfo System::on_get_system_info() const
{
    return {
        .name = "ESPocket",
        .version = "0.3.0",
    };
}

std::expected<void, std::string> System::on_init()
{
    auto hello = std::make_shared<HelloApp>();
    auto declaration = hello->get_page_declaration();
    if (declaration.app_id != hello->get_manifest().id) {
        return std::unexpected("Hello Native Page declaration App ID does not match its manifest");
    }
    auto navigator = PageNavigator::create(
        std::move(declaration),
        [weak_hello = std::weak_ptr<HelloApp>(hello)](std::string_view from, std::string_view to) {
            auto app = weak_hello.lock();
            return app && app->present_page(from, to);
        }
    );
    if (!navigator) {
        return std::unexpected("Invalid Hello Native Page declaration");
    }
    hello_navigator_ = std::make_shared<PageNavigator>(std::move(*navigator));
    hello_navigator_->set_availability_handler([this](bool default_visible, bool edge_enabled) {
        default_back_visible_.store(default_visible, std::memory_order_release);
        edge_back_enabled_.store(edge_enabled, std::memory_order_release);
    });
    hello->set_navigator(hello_navigator_);
    auto hello_result = install_app(hello);
    if (!hello_result) {
        return std::unexpected("Failed to install Hello Native: " + hello_result.error());
    }
    hello_id_ = *hello_result;
    ESP_LOGI(TAG, "Hello Native installed");

    auto settings_result = install_app(
                               std::make_shared<
                                   esp_brookesia::app::settings::SettingsApp
                               >()
                           );
    if (!settings_result) {
        return std::unexpected(
            "Failed to install Settings: " + settings_result.error()
        );
    }
    ESP_LOGI(TAG, "Settings installed");

    auto store_result = install_app(
                            std::make_shared<
                                esp_brookesia::app::app_store::AppStoreApp
                            >()
                        );
    if (!store_result) {
        return std::unexpected(
            "Failed to install App Store: " + store_result.error()
        );
    }
    ESP_LOGI(TAG, "App Store installed");

    power_key_monitor_ = std::make_unique<PowerKeyMonitor>();
    shell_ = std::make_shared<CircularShell>(
        display_output_id_,
        [this]() {
            return power_key_monitor_ ? power_key_monitor_->short_press_count() : 0;
        },
        [this]() {
            return display_on_.load(std::memory_order_acquire);
        },
        [this]() {
            return foreground_app_id_.load(std::memory_order_acquire) !=
                   esp_brookesia::system::core::INVALID_APP_ID;
        },
        [this]() {
            handle_power_short_press();
        },
        [this]() {
            handle_screen_timeout();
        },
        [this](std::string_view manifest_id, ShellSurface source) {
            return launch_app(manifest_id, source);
        },
        [this]() {
            handle_back();
        },
        [this](
            esp_brookesia::system::core::AppId app_id,
            esp_brookesia::system::core::KeyboardRequestId request_id,
            bool confirmed,
            std::string text
        ) {
            auto result = complete_app_keyboard(
                              app_id,
                              request_id,
                              confirmed,
                              std::move(text)
                          );
            if (!result) {
                ESP_LOGW(TAG, "Failed to complete keyboard request: %s", result.error().c_str());
            }
        },
        [this]() {
            const bool hello_foreground = foreground_app_id_.load(std::memory_order_acquire) ==
                                          hello_id_;
            return CircularShell::BackUiState{
                .default_visible = hello_foreground &&
                                   default_back_visible_.load(std::memory_order_acquire),
                .edge_enabled = hello_foreground &&
                                edge_back_enabled_.load(std::memory_order_acquire),
            };
        },
        [this]() {
            handle_back_timeout();
        }
    );
    auto result = install_app(shell_);
    if (!result) {
        shell_.reset();
        return std::unexpected("Failed to install Circular Shell: " + result.error());
    }
    shell_id_ = *result;
    ESP_LOGI(TAG, "Circular Shell installed");
    return {};
}

std::expected<void, std::string> System::on_start()
{
    stopping_.store(false, std::memory_order_release);
    foreground_app_id_.store(
        esp_brookesia::system::core::INVALID_APP_ID,
        std::memory_order_release
    );
    foreground_token_->store(0, std::memory_order_release);
    if (shell_id_ == esp_brookesia::system::core::INVALID_APP_ID) {
        return std::unexpected("Circular Shell is not installed");
    }

#if CONFIG_ESPOCKET_M2_LIFECYCLE_STRESS
    auto apps = list_apps();
    auto hello = std::find_if(apps.begin(), apps.end(), [](const auto &app) {
        return app.manifest.id == "espocket.app.hello";
    });
    if (hello == apps.end()) {
        return std::unexpected("Hello Native is not installed for M2 lifecycle stress");
    }
    auto stress_result = run_m2_lifecycle_stress(*this, hello->app_id);
    if (!stress_result) {
        return stress_result;
    }
#endif

    auto result = start_app(shell_id_);
    if (!result) {
        return std::unexpected("Failed to start Circular Shell: " + result.error());
    }
    auto power_result = power_key_monitor_->start();
    if (!power_result) {
        (void)stop_app(shell_id_);
        return std::unexpected("Failed to start PWR input: " + power_result.error());
    }
    display_on_.store(true, std::memory_order_release);
    resume_app_id_ = esp_brookesia::system::core::INVALID_APP_ID;
    return {};
}

std::expected<void, std::string> System::on_app_started(
    const esp_brookesia::system::core::AppInfo &app
)
{
    if (stopping_.load(std::memory_order_acquire)) {
        return std::unexpected("ESPocket System is stopping");
    }
    if (app.app_id == shell_id_ || !app.manifest.visible) {
        return {};
    }

    if (app.manifest.id == "espocket.app.hello" && hello_navigator_) {
        auto result = hello_navigator_->start();
        if (!result) {
            return std::unexpected("Failed to start Hello Native Page Navigator");
        }
    }

    foreground_app_id_.store(app.app_id, std::memory_order_release);
    do {
        ++foreground_generation_;
    } while (foreground_generation_ == 0);
    foreground_token_->store(foreground_generation_, std::memory_order_release);
    lifecycle_restore_pending_ = false;
    return {};
}

void System::on_app_start_failed(
    const esp_brookesia::system::core::AppInfo &app,
    std::string_view reason
)
{
    if (app.manifest.id == "espocket.app.hello" && hello_navigator_) {
        hello_navigator_->stop();
    }
    ESP_LOGW(
        TAG,
        "App start failed: manifest=%s reason=%.*s",
        app.manifest.id.c_str(),
        static_cast<int>(reason.size()),
        reason.data()
    );
    restore_home_after_lifecycle(app);
}

void System::on_app_stopped(const esp_brookesia::system::core::AppInfo &app)
{
    if (app.manifest.id == "espocket.app.hello" && hello_navigator_) {
        hello_navigator_->stop();
    }
    restore_home_after_lifecycle(app);
}

void System::on_app_stop_failed(
    const esp_brookesia::system::core::AppInfo &app,
    std::string_view reason
)
{
    if (app.manifest.id == "espocket.app.hello" && hello_navigator_) {
        hello_navigator_->stop();
    }
    ESP_LOGW(
        TAG,
        "App stop failed: manifest=%s reason=%.*s",
        app.manifest.id.c_str(),
        static_cast<int>(reason.size()),
        reason.data()
    );
    if (app.manifest.kind == esp_brookesia::system::core::AppKind::Runtime) {
        runtime_stop_failed_.store(true, std::memory_order_release);
        ESP_LOGE(TAG, "Keyboard input disabled after Runtime stop failure");
    }
    restore_home_after_lifecycle(app);
}

std::expected<void, std::string> System::on_show_app_keyboard(
    esp_brookesia::system::core::AppId app_id,
    esp_brookesia::system::core::KeyboardRequestId request_id,
    const esp_brookesia::system::core::KeyboardRequestOptions &options
)
{
    if (runtime_stop_failed_.load(std::memory_order_acquire)) {
        return std::unexpected("Keyboard input is disabled until restart after Runtime stop failure");
    }
    auto app = get_app(app_id);
    if (!app.has_value()) {
        return std::unexpected("Keyboard owner app is not installed");
    }
    if (app->state != esp_brookesia::system::core::AppState::Running) {
        return std::unexpected("Keyboard input requires a running owner app");
    }
    if (!shell_) {
        return std::unexpected("Circular Shell is unavailable for keyboard input");
    }
    return shell_->show_keyboard(app_id, request_id, options);
}

void System::on_hide_app_keyboard(
    esp_brookesia::system::core::AppId app_id,
    esp_brookesia::system::core::KeyboardRequestId request_id
)
{
    if (shell_) {
        shell_->hide_keyboard(app_id, request_id);
    }
}

void System::handle_power_short_press()
{
    if (stopping_.load(std::memory_order_acquire) || !shell_) {
        return;
    }

    if (!display_on_.load(std::memory_order_acquire)) {
        auto result = set_display_on(true);
        if (!result) {
            ESP_LOGW(TAG, "PWR wake failed: %s", result.error().c_str());
            return;
        }
        if (resume_app_id_ != esp_brookesia::system::core::INVALID_APP_ID) {
            auto active = get_active_app();
            auto app = get_app(resume_app_id_);
            if (!active.has_value() || active->app_id != resume_app_id_ ||
                    !app.has_value() || app->state != esp_brookesia::system::core::AppState::Running) {
                show_watch_face();
            }
        }
        resume_app_id_ = esp_brookesia::system::core::INVALID_APP_ID;
        ESP_LOGI(TAG, "M6 display state: Wake");
        return;
    }

    auto active = get_active_app();
    if (active.has_value() && active->app_id != shell_id_ && active->manifest.visible) {
        lifecycle_restore_surface_ = ShellSurface::WatchFace;
        lifecycle_restore_pending_ = true;
        auto result = stop_app(active->app_id);
        if (!result) {
            ESP_LOGW(TAG, "PWR Home failed to stop app: %s", result.error().c_str());
        }
        return;
    }

    if (!shell_->is_watch_face()) {
        show_watch_face();
        return;
    }

#if CONFIG_ESPOCKET_M6_RESOURCE_TRACE
    static uint32_t resource_sample = 0;
    ++resource_sample;
    ESP_LOGI(
        TAG,
        "M6_RESOURCE sample=%" PRIu32 " internal_free=%zu psram_free=%zu internal_largest=%zu psram_largest=%zu",
        resource_sample,
        heap_caps_get_free_size(MALLOC_CAP_INTERNAL),
        heap_caps_get_free_size(MALLOC_CAP_SPIRAM),
        heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL),
        heap_caps_get_largest_free_block(MALLOC_CAP_SPIRAM)
    );
#endif

    auto result = set_display_on(false);
    if (!result) {
        ESP_LOGW(TAG, "PWR screen-off failed: %s", result.error().c_str());
    }
}

std::expected<void, std::string> System::launch_app(
    std::string_view manifest_id,
    ShellSurface source
)
{
    auto apps = list_apps();
    auto app = std::find_if(apps.begin(), apps.end(), [manifest_id](const auto &candidate) {
        return candidate.manifest.id == manifest_id;
    });
    if (app == apps.end()) {
        return std::unexpected("App is not installed: " + std::string(manifest_id));
    }
    launch_source_ = source;
    lifecycle_restore_surface_ = source;
    lifecycle_restore_pending_ = true;
    auto result = start_app(app->app_id);
    if (!result) {
        restore_surface(source);
        lifecycle_restore_pending_ = false;
        return result;
    }
    return {};
}

void System::handle_back()
{
    if (stopping_.load(std::memory_order_acquire) || !shell_) {
        return;
    }
    auto active = get_active_app();
    if (!active.has_value() || active->app_id == shell_id_ || !active->manifest.visible) {
        if (shell_->current_surface() != ShellSurface::WatchFace) {
            restore_surface(ShellSurface::WatchFace);
        }
        return;
    }

    if (active->manifest.id == "espocket.app.hello" && hello_navigator_) {
        if (!hello_navigator_->edge_back_enabled()) {
            return;
        }
        auto result = hello_navigator_->request_back(
            static_cast<uint64_t>(esp_timer_get_time() / 1000)
        );
        if (!result) {
            ESP_LOGW(TAG, "App Page Back failed: %d", static_cast<int>(result.error()));
        }
    }
}

void System::handle_back_timeout()
{
    if (!hello_navigator_) {
        return;
    }
    const auto expired = hello_navigator_->expire_back(
        static_cast<uint64_t>(esp_timer_get_time() / 1000)
    );
    if (expired) {
        ESP_LOGW(TAG, "App Back confirmation timed out: %d", static_cast<int>(*expired));
    }
}

void System::handle_screen_timeout()
{
    if (stopping_.load(std::memory_order_acquire) ||
            !display_on_.load(std::memory_order_acquire)) {
        return;
    }
    auto result = set_display_on(false);
    if (!result) {
        ESP_LOGW(TAG, "Automatic screen-off failed: %s", result.error().c_str());
        return;
    }

#if CONFIG_ESPOCKET_M6_RECLAIM_ON_TIMEOUT_TEST
    if (resume_app_id_ != esp_brookesia::system::core::INVALID_APP_ID) {
        const auto target = resume_app_id_;
        auto stop_result = stop_app(target);
        if (!stop_result) {
            ESP_LOGE(TAG, "M6_RECLAIM_TEST failed to stop App: %s", stop_result.error().c_str());
        } else {
            ESP_LOGI(TAG, "M6_RECLAIM_TEST stopped resume target app_id=%" PRIu32, target);
        }
    }
#endif
}

std::expected<void, std::string> System::set_display_on(bool on)
{
    if (!shell_) {
        return std::unexpected("Circular Shell is unavailable");
    }
    if (display_on_.load(std::memory_order_acquire) == on) {
        return {};
    }

    if (!on) {
        auto active = get_active_app();
        resume_app_id_ = active.has_value() && active->app_id != shell_id_ && active->manifest.visible ?
                         active->app_id : esp_brookesia::system::core::INVALID_APP_ID;
        auto input_result = shell_->set_display_on(false);
        if (!input_result) {
            return input_result;
        }
    }

    auto backlight_result = DisplayHelper::call_function_sync(
                                DisplayHelper::FunctionId::SetBacklightOnOff,
                                static_cast<double>(display_output_id_),
                                on,
                                esp_brookesia::service::helper::Timeout(DISPLAY_TIMEOUT_MS)
                            );
    if (!backlight_result) {
        if (!on) {
            (void)shell_->set_display_on(true);
        }
        return std::unexpected("Failed to change display power: " + backlight_result.error());
    }

    if (on) {
        auto input_result = shell_->set_display_on(true);
        if (!input_result) {
            return input_result;
        }
    }
    display_on_.store(on, std::memory_order_release);
    ESP_LOGI(TAG, "M6 display state: %s", on ? "On" : "Off");
    return {};
}

void System::show_watch_face()
{
    if (!shell_) {
        return;
    }
    auto result = shell_->show_watch_face();
    if (!result) {
        ESP_LOGW(TAG, "Failed to show Watch Face: %s", result.error().c_str());
    } else {
        ESP_LOGI(TAG, "M6 Home: Watch Face");
    }
}

void System::restore_surface(ShellSurface surface)
{
    if (!shell_) {
        return;
    }
    auto result = shell_->show_surface(surface);
    if (!result) {
        ESP_LOGW(TAG, "Failed to restore Shell surface: %s", result.error().c_str());
        if (surface != ShellSurface::WatchFace) {
            show_watch_face();
        }
    }
}

void System::clear_foreground(
    const esp_brookesia::system::core::AppInfo &app
)
{
    auto expected = app.app_id;
    if (!foreground_app_id_.compare_exchange_strong(
                expected,
                esp_brookesia::system::core::INVALID_APP_ID,
                std::memory_order_acq_rel
            )) {
        return;
    }
    foreground_token_->store(0, std::memory_order_release);
}

void System::restore_home_after_lifecycle(
    const esp_brookesia::system::core::AppInfo &app
)
{
    clear_foreground(app);
    if (stopping_.load(std::memory_order_acquire) || app.app_id == shell_id_ ||
            !app.manifest.visible || !shell_) {
        return;
    }

    auto active = get_active_app();
    if (active.has_value() && active->app_id != shell_id_ && active->manifest.visible) {
        return;
    }

    auto shell = get_app(shell_id_);
    if (!shell.has_value() || shell->state != esp_brookesia::system::core::AppState::Running) {
        return;
    }
    const auto surface = lifecycle_restore_pending_ ? lifecycle_restore_surface_ : ShellSurface::WatchFace;
    lifecycle_restore_pending_ = false;
    restore_surface(surface);
}

void System::on_stop()
{
    stopping_.store(true, std::memory_order_release);
    foreground_token_->store(0, std::memory_order_release);
    if (power_key_monitor_) {
        power_key_monitor_->stop();
    }

    if (shell_id_ != esp_brookesia::system::core::INVALID_APP_ID) {
        auto shell_result = stop_app(shell_id_);
        if (!shell_result) {
            ESP_LOGW(TAG, "Failed to stop Circular Shell: %s", shell_result.error().c_str());
        }
    }

    const auto app_id = foreground_app_id_.exchange(
                            esp_brookesia::system::core::INVALID_APP_ID,
                            std::memory_order_acq_rel
                        );
    if (app_id != esp_brookesia::system::core::INVALID_APP_ID) {
        auto app_result = stop_app(app_id);
        if (!app_result) {
            ESP_LOGW(TAG, "Failed to stop foreground app: %s", app_result.error().c_str());
        }
    }
}

void System::on_deinit()
{
    shell_.reset();
    power_key_monitor_.reset();
    shell_id_ = esp_brookesia::system::core::INVALID_APP_ID;
    foreground_app_id_.store(
        esp_brookesia::system::core::INVALID_APP_ID,
        std::memory_order_release
    );
    foreground_token_->store(0, std::memory_order_release);
    stopping_.store(false, std::memory_order_release);
    display_on_.store(true, std::memory_order_release);
    resume_app_id_ = esp_brookesia::system::core::INVALID_APP_ID;
    launch_source_ = ShellSurface::WatchFace;
    lifecycle_restore_surface_ = ShellSurface::WatchFace;
    lifecycle_restore_pending_ = false;
    if (display_started_) {
        DisplaySource::get_instance().stop();
        display_started_ = false;
    }
    display_binding_.release();
}

std::expected<void, std::string> System::start_display()
{
    if (!DisplayHelper::is_available()) {
        return std::unexpected("Display service is unavailable");
    }

    auto &service_manager = esp_brookesia::service::ServiceManager::get_instance();
    display_binding_ = service_manager.bind(DisplayHelper::get_name().data());
    if (!display_binding_.is_valid()) {
        return std::unexpected("Failed to bind Display service");
    }

    auto outputs_json = DisplayHelper::call_function_sync<boost::json::array>(
                            DisplayHelper::FunctionId::GetOutputs,
                            esp_brookesia::service::helper::Timeout(DISPLAY_TIMEOUT_MS)
                        );
    if (!outputs_json) {
        return std::unexpected("Failed to get Display outputs: " + outputs_json.error());
    }

    std::vector<DisplayHelper::OutputInfo> outputs;
    if (!BROOKESIA_DESCRIBE_FROM_JSON(boost::json::value(*outputs_json), outputs)) {
        return std::unexpected("Failed to parse Display outputs");
    }
    auto output = std::find_if(outputs.begin(), outputs.end(), [](const auto &candidate) {
        return candidate.width > 0 && candidate.height > 0 && candidate.touch.has_value();
    });
    if (output == outputs.end()) {
        return std::unexpected("No display output with touch support is available");
    }

    // The backlight command shares the panel SPI bus. Complete it before the LVGL worker starts
    // submitting frames so Display and LVGL locks cannot be acquired in opposite orders.
    if (output->backlight.has_value()) {
        auto backlight_result = DisplayHelper::call_function_sync(
                                    DisplayHelper::FunctionId::SetBacklightOnOff,
                                    static_cast<double>(output->id),
                                    true,
                                    esp_brookesia::service::helper::Timeout(DISPLAY_TIMEOUT_MS)
                                );
        if (!backlight_result) {
            return std::unexpected("Failed to turn on Display backlight: " + backlight_result.error());
        }
    }

    esp_brookesia::gui::lvgl::DisplaySourceConfig source_config;
    source_config.output_name = output->name;
    auto &source = DisplaySource::get_instance();
    if (!source.start(source_config)) {
        return std::unexpected("Failed to start LVGL Display source");
    }
    display_started_ = true;

    auto active_result = DisplayHelper::call_function_sync(
                             DisplayHelper::FunctionId::SetActiveSourceRole,
                             output->name,
                             std::string(esp_brookesia::gui::lvgl::DISPLAY_SOURCE_ROLE),
                             esp_brookesia::service::helper::Timeout(DISPLAY_TIMEOUT_MS)
                         );
    if (!active_result) {
        return std::unexpected("Failed to activate LVGL Display source: " + active_result.error());
    }

    display_width_ = output->width;
    display_height_ = output->height;
    display_output_id_ = output->id;
    ESP_LOGI(
        TAG,
        "Display ready: %s (%" PRIu32 "x%" PRIu32 ")",
        output->name.c_str(),
        display_width_,
        display_height_
    );
    return {};
}

} // namespace espocket
