#include "system_internal.hpp"

namespace espocket {

System::System()
    : launch_source_(ShellSurface::WatchFace),
      lifecycle_restore_surface_(ShellSurface::WatchFace)
{}

System::~System()
{
    stop_runtime_navigation();
}

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
        stop_runtime_navigation();
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
        .version = esp_app_get_description()->version,
    };
}

std::expected<void, std::string> System::on_init()
{
    init_runtime_navigation();
    developer_mode_ = make_device_developer_mode();
    if (auto restored = developer_mode_->restore(); !restored) {
        ESP_LOGW(TAG, "Developer mode disabled after storage read failure: %s",
                 restored.error().c_str());
    }
    init_cards();
    test_power_input_ = std::make_unique<TestInputQueue>();
    test_touch_input_ = std::make_unique<TouchInputSequence>(*test_power_input_,
        [this](const TouchInputStep &step, bool first) -> std::expected<void, std::string> {
            if (!shell_) { return std::unexpected("invalid_state"); }
            return shell_->inject_synthetic_touch(step.x, step.y, step.pressed, first);
        }, [this](bool cancelled) -> std::expected<void, std::string> {
            return shell_ ? shell_->finish_synthetic_touch(cancelled) :
                            std::expected<void, std::string>{};
        });
    test_adapter_ = std::make_unique<InteractionTestAdapter>(
        developer_mode_, [this]() { return read_test_snapshot(); },
        [this]() -> std::expected<void, std::string> {
            if (stopping_.load(std::memory_order_acquire) || !test_power_input_ ||
                    !developer_mode_->enabled()) {
                return std::unexpected("invalid_state");
            }
            return test_power_input_->enqueue(static_cast<uint64_t>(esp_timer_get_time() / 1000),
                                               foreground_token_->load(std::memory_order_acquire));
        },
        [this]() -> std::expected<void, std::string> {
            return release_test_input();
        },
        [this](std::vector<TouchInputStep> steps) { return start_test_touch(std::move(steps)); },
        [this]() { return tick_test_touch(); }
    );

    auto hello = std::make_shared<HelloApp>();
    auto hello_result = install_navigated_app(
        hello, hello->get_page_declaration(),
        [weak_hello = std::weak_ptr<HelloApp>(hello)](std::string_view from, std::string_view to) {
            auto app = weak_hello.lock();
            return app && app->present_page(from, to);
        }, hello->get_card_factory()
    );
    if (!hello_result) {
        return std::unexpected("Failed to install Hello Native: " + hello_result.error());
    }
    hello_result->navigator->set_diagnostic_handler([](NavigationError error, std::string_view target) {
        if (error == NavigationError::TargetUnavailable) {
            ESP_LOGW(TAG, "App Card target unavailable: %.*s", static_cast<int>(target.size()),
                     target.data());
        }
    });
    hello->set_navigator(hello_result->navigator);
    ESP_LOGI(TAG, "Hello Native installed");

    settings_adapter_ = std::make_shared<SettingsNavigationAdapter>(
        std::make_shared<esp_brookesia::app::settings::SettingsApp>()
    );
    auto settings_result = install_app(settings_adapter_);
    if (!settings_result) {
        return std::unexpected(
            "Failed to install Settings: " + settings_result.error()
        );
    }
    settings_id_ = *settings_result;
    ESP_LOGI(TAG, "Settings installed");

    auto store = std::make_shared<esp_brookesia::app::app_store::AppStoreApp>();
    const auto store_manifest = store->get_manifest();
    auto store_result = install_navigated_app(
        store, PageDeclaration{
            .app_id = store_manifest.id,
            .root_page_id = "store.root",
            .page_ids = {"store.root"},
            .cards = {},
            .back_presentation = BackPresentation::Framework,
            .uses_standard_back_control = false,
        },
        [](std::string_view, std::string_view) { return true; }
    );
    if (!store_result) {
        return std::unexpected("Failed to install App Store: " + store_result.error());
    }
    ESP_LOGI(TAG, "App Store installed");

    power_key_monitor_ = std::make_unique<PowerKeyMonitor>();
    shell_ = std::make_shared<CircularShell>(
        display_output_id_,
        ShellHost{
        .display_on = [this]() {
            return display_on_.load(std::memory_order_acquire);
        },
        .app_visible = [this]() {
            return foreground_app_id_.load(std::memory_order_acquire) !=
                   esp_brookesia::system::core::INVALID_APP_ID;
        },
        .screen_timeout = [this]() {
            handle_screen_timeout();
        },
        .launch_app = [this](std::string_view manifest_id, ShellSurface source) {
            return launch_app(manifest_id, source);
        },
        .back = [this]() {
            handle_back();
        },
        .keyboard_result = [this](
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
        .back_ui = [this]() {
            const auto foreground = foreground_app_id_.load(std::memory_order_acquire);
            if (foreground == settings_id_ && settings_adapter_) {
                return CircularShell::BackUiState{
                    .default_visible = false,
                    .edge_enabled = settings_adapter_->edge_back_enabled(),
                };
            }
            const bool registered_foreground = navigator_for(foreground) != nullptr;
            return CircularShell::BackUiState{
                .default_visible = registered_foreground &&
                                   default_back_visible_.load(std::memory_order_acquire),
                .edge_enabled = registered_foreground &&
                                edge_back_enabled_.load(std::memory_order_acquire),
            };
        },
        .expire_back = [this]() {
            handle_back_timeout();
        },
        .developer_mode = CircularShell::DeveloperModeControl{
            .enabled = [mode = developer_mode_]() { return mode->enabled(); },
            .set_enabled = [adapter = test_adapter_.get()](bool enabled) {
                return adapter->set_developer_mode(enabled);
            },
        },
        .tick = [this]() { poll_system_input(); },
        .card_step = [this](bool left, bool inward) { return step_card(left, inward); },
        .surface_changed = [this](ShellSurface surface) { card_surface_changed(surface); },
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
    init_runtime_navigation();
    if (card_actions_) card_actions_->close();
    card_actions_ = std::make_shared<NavigationRequestQueue>();
    if (card_store_) {
        if (auto restored = card_store_->restore(); !restored) {
            ESP_LOGW(TAG, "Card configuration not restored: %s", restored.error().c_str());
        }
    }
    stopping_.store(false, std::memory_order_release);
    if (test_power_input_) { test_power_input_->cancel_pending(); }
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
    if (test_adapter_) {
        auto started = test_adapter_->start();
        if (!started) {
            ESP_LOGW(TAG, "USB Test Adapter unavailable: %s", started.error().c_str());
        }
    }
    return {};
}

void System::on_stop()
{
    stopping_.store(true, std::memory_order_release);
    stop_runtime_navigation();
    pause_card();
    if (card_actions_) card_actions_->close();
    if (test_adapter_) {
        test_adapter_->stop();
    }
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
    stop_runtime_navigation();
    if (card_actions_) card_actions_->close();
    card_session_.reset();
    card_actions_.reset();
    card_factories_.clear();
    shell_.reset();
    settings_adapter_.reset();
    card_store_.reset();
    cards_.reset();
    settings_id_ = esp_brookesia::system::core::INVALID_APP_ID;
    decltype(page_navigators_) retired_navigators;
    {
        std::lock_guard lock(page_navigators_mutex_);
        retired_navigators = std::move(page_navigators_);
        runtime_pages_.clear();
    }
    for (const auto &[app_id, navigator] : retired_navigators) {
        navigator->stop();
        navigator->set_availability_handler({});
    }
    power_key_monitor_.reset();
    test_touch_input_.reset();
    test_power_input_.reset();
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

} // namespace espocket
