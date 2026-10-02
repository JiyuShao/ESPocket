#include "shell_internal.hpp"

namespace espocket {

CircularShell::CircularShell(
    uint32_t display_output_id,
    ShellHost host
)
    : display_output_id_(display_output_id),
      host_(std::move(host))
{}

esp_brookesia::system::core::AppManifest CircularShell::get_manifest() const
{
    esp_brookesia::system::core::AppManifest manifest{};
    manifest.id = "espocket.shell.circular";
    manifest.name = "Circular Shell";
    manifest.localized_names = {
        {"en", "Circular Shell"},
        {"zh_CN", "圆形桌面"},
    };
    manifest.version = "0.1.0";
    manifest.kind = esp_brookesia::system::core::AppKind::Native;
    manifest.visible = false;
    return manifest;
}

std::expected<void, std::string> CircularShell::on_start(
    esp_brookesia::system::core::AppContext &context
)
{
    context_ = &context;
    keyboard_state_ = std::make_shared<KeyboardState>();
    back_overlay_state_ = std::make_shared<BackOverlayState>();

    for (const auto action : {
             OPEN_HELLO_NATIVE_ACTION,
             OPEN_HELLO_RUNTIME_ACTION,
             OPEN_SETTINGS_ACTION,
             OPEN_SETTINGS_CARD_ACTION,
             OPEN_SETTINGS_QUICK_ACTION,
             OPEN_APP_STORE_ACTION,
             STEP_BRIGHTNESS_ACTION,
             STEP_BRIGHTNESS_QUICK_ACTION,
             TOGGLE_WIFI_ACTION,
             TOGGLE_DEVELOPER_MODE_ACTION,
         }) {
        auto action_result = context.gui().subscribe_action(action);
        if (!action_result) {
            keyboard_state_.reset();
            context_ = nullptr;
            return std::unexpected("Failed to subscribe Launcher action: " + action_result.error());
        }
    }

    home_gesture_state_ = std::make_shared<HomeGestureState>();
    last_activity_generation_ = 0;
    last_activity_us_ = esp_timer_get_time();
    screen_timeout_latched_ = false;
    auto gesture_result = configure_home_gesture();
    if (!gesture_result) {
        home_gesture_state_.reset();
        keyboard_state_.reset();
        context_ = nullptr;
        return gesture_result;
    }

    auto home_timer = context.timer().start_periodic(
                          HOME_INTENT_TIMER,
                          HOME_INTENT_INTERVAL_MS
                      );
    if (!home_timer) {
        gesture_connection_.disconnect();
        display_binding_.release();
        home_gesture_state_.reset();
        keyboard_state_.reset();
        context_ = nullptr;
        return std::unexpected(
            "Failed to start Home intent timer: " + home_timer.error()
        );
    }
    home_intent_timer_id_ = *home_timer;

    callback_state_ = std::make_shared<CallbackState>();
    callback_state_->owner = this;
    start_status();
    ESP_LOGI(SHELL_TAG, "Circular Shell started");
    return {};
}

std::expected<void, std::string> CircularShell::on_stop(
    esp_brookesia::system::core::AppContext &context
)
{
    (void)context;
    if (keyboard_state_) {
        esp_brookesia::system::core::AppId app_id =
            esp_brookesia::system::core::INVALID_APP_ID;
        esp_brookesia::system::core::KeyboardRequestId request_id =
            esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID;
        {
            std::lock_guard lock(keyboard_state_->mutex);
            app_id = keyboard_state_->app_id;
            request_id = keyboard_state_->request_id;
        }
        if (request_id != esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID) {
            hide_keyboard(app_id, request_id);
        }
    }
    sync_default_back(false);
    sync_card_hint(false);
    gesture_connection_.disconnect();
    if (home_intent_timer_id_ != esp_brookesia::system::core::INVALID_TIMER_ID) {
        (void)context.timer().stop(home_intent_timer_id_);
    }
    home_intent_timer_id_ = esp_brookesia::system::core::INVALID_TIMER_ID;
    home_gesture_state_.reset();
    stop_status();
    display_binding_.release();
    context_ = nullptr;
    keyboard_state_.reset();
    back_overlay_state_.reset();
    callback_state_.reset();
    return {};
}

std::expected<void, std::string> CircularShell::on_action(
    esp_brookesia::system::core::AppContext &context,
    std::string_view action
)
{
    (void)context;
    // PROTOTYPE: a completed pull must not also open the touched list row.
    if (current_surface() == ShellSurface::Launcher && home_gesture_state_ &&
            home_gesture_state_->launcher_pull_distance.load(std::memory_order_acquire) >=
                home_gesture_state_->launcher_return_threshold.load(std::memory_order_acquire)) {
        return {};
    }
    if (action == OPEN_HELLO_NATIVE_ACTION) {
        return open_app(HELLO_NATIVE_MANIFEST_ID, "Hello Native");
    }
    if (action == OPEN_HELLO_RUNTIME_ACTION) {
        return open_app(HELLO_RUNTIME_MANIFEST_ID, "Hello Runtime");
    }
    if (action == OPEN_SETTINGS_ACTION || action == OPEN_SETTINGS_CARD_ACTION ||
        action == OPEN_SETTINGS_QUICK_ACTION) {
        return open_app(SETTINGS_MANIFEST_ID, "Settings");
    }
    if (action == OPEN_APP_STORE_ACTION) {
        return open_app(APP_STORE_MANIFEST_ID, "App Store");
    }
    if (action == STEP_BRIGHTNESS_ACTION || action == STEP_BRIGHTNESS_QUICK_ACTION) {
        auto result = step_brightness();
        if (!result) {
            set_status_text(BRIGHTNESS_CARD_PATH, "Brightness: unavailable");
            set_status_text(QUICK_BRIGHTNESS_PATH, "Brightness: unavailable");
        }
        return result;
    }
    if (action == TOGGLE_WIFI_ACTION) {
        auto result = toggle_wifi();
        if (!result) {
            set_status_text(QUICK_WIFI_PATH, "Wi-Fi: unavailable");
        }
        return result;
    }
    if (action == TOGGLE_DEVELOPER_MODE_ACTION) {
        if (!host_.developer_mode.enabled || !host_.developer_mode.set_enabled) {
            return std::unexpected("Developer mode control is unavailable");
        }
        auto result = host_.developer_mode.set_enabled(!host_.developer_mode.enabled());
        refresh_developer_mode();
        return result;
    }
    return {};
}

std::expected<void, std::string> CircularShell::on_timer(
    esp_brookesia::system::core::AppContext &context,
    esp_brookesia::system::core::TimerId timer_id,
    std::string_view name
)
{
    (void)context;
    if (timer_id == home_intent_timer_id_ && name == HOME_INTENT_TIMER) {
        if (host_.expire_back) {
            host_.expire_back();
        }
        if (back_overlay_state_) {
            const bool clicked = back_overlay_state_->clicked.exchange(
                                     false, std::memory_order_acq_rel
                                 );
            if (clicked && host_.back) {
                host_.back();
            }
            bool keyboard_active = false;
            if (keyboard_state_) {
                std::lock_guard lock(keyboard_state_->mutex);
                keyboard_active = keyboard_state_->request_id !=
                                  esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID;
            }
            const bool visible = host_.back_ui && host_.back_ui().default_visible &&
                                 !keyboard_active;
            sync_default_back(visible);
            const auto surface = current_surface();
            sync_card_hint(!keyboard_active && !(host_.app_visible && host_.app_visible()) &&
                (surface == ShellSurface::LeftAppCard || surface == ShellSurface::RightAppCard));
        }
        if (keyboard_state_ && host_.keyboard_result) {
            esp_brookesia::system::core::AppId app_id =
                esp_brookesia::system::core::INVALID_APP_ID;
            esp_brookesia::system::core::KeyboardRequestId request_id =
                esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID;
            bool confirmed = false;
            std::string text;
            {
                std::lock_guard lock(keyboard_state_->mutex);
                if (keyboard_state_->result_pending) {
                    app_id = keyboard_state_->app_id;
                    request_id = keyboard_state_->request_id;
                    confirmed = keyboard_state_->confirmed;
                    text = std::move(keyboard_state_->text);
                    keyboard_state_->result_pending = false;
                }
            }
            if (request_id != esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID) {
                hide_keyboard(app_id, request_id);
                host_.keyboard_result(app_id, request_id, confirmed, std::move(text));
            }
        }
        if (host_.tick) {
            host_.tick();
        }
        if (home_gesture_state_) {
            const auto activity = home_gesture_state_->activity_generation.load(std::memory_order_acquire);
            if (activity != last_activity_generation_) {
                last_activity_generation_ = activity;
                last_activity_us_ = esp_timer_get_time();
                screen_timeout_latched_ = false;
            }
            if (current_surface() == ShellSurface::Launcher &&
                    (!host_.app_visible || !host_.app_visible())) {
                {
                    LvglLock lock;
                    if (lock) {
                        if (auto *launcher = find_launcher_view(lv_screen_active()); launcher != nullptr) {
                            home_gesture_state_->launcher_scroll_top.store(
                                lv_obj_get_scroll_top(launcher), std::memory_order_release
                            );
                        }
                    }
                }
                const int32_t pull = home_gesture_state_->launcher_pull_distance.load(
                                         std::memory_order_acquire
                                     );
                const int32_t threshold = home_gesture_state_->launcher_return_threshold.load(
                                              std::memory_order_acquire
                                          );
                const uint8_t visual = pull <= 0 ? 0 : (pull >= threshold ? 2 : 1);
                if (visual != launcher_pull_visual_) {
                    launcher_pull_visual_ = visual;
                    set_status_text(
                        LAUNCHER_PULL_PATH,
                        visual == 2 ? "↓  Release for Home" :
                        visual == 1 ? "↓  Keep pulling" : "↓  Pull for Home"
                    );
                }
                const int32_t height = 28 + std::min<int32_t>(32, pull / 3);
                if (height != launcher_pull_height_ && context_ != nullptr) {
                    launcher_pull_height_ = height;
                    auto result = context_->gui().set_binding_value(
                                      LAUNCHER_PULL_PATH,
                                      "pullHeight",
                                      std::to_string(height) + "dp"
                                  );
                    if (!result) {
                        ESP_LOGW(SHELL_TAG, "Launcher pull feedback failed: %s", result.error().c_str());
                    }
                }
            }
            const auto intent = static_cast<GestureIntent>(
                                    home_gesture_state_->pending_gesture.exchange(
                                        static_cast<uint8_t>(GestureIntent::None),
                                        std::memory_order_acq_rel
                                    )
                                );
            if (intent != GestureIntent::None) {
                LvglLock lock;
                if (!lock) return std::unexpected("Unable to consume navigation touch");
                // A screen change must not turn the held swipe into a new button press.
                for (auto *input = lv_indev_get_next(nullptr); input != nullptr; input = lv_indev_get_next(input)) {
                    if (lv_indev_get_type(input) == LV_INDEV_TYPE_POINTER) lv_indev_wait_release(input);
                }
            }
            std::expected<void, std::string> result{};
            switch (intent) {
            case GestureIntent::WatchFace:
                result = show_surface(ShellSurface::WatchFace);
                break;
            case GestureIntent::BatteryCard:
                result = host_.card_step ? host_.card_step(true, false) : show_surface(ShellSurface::BatteryCard);
                break;
            case GestureIntent::BrightnessCard:
                result = host_.card_step ? host_.card_step(false, false) : show_surface(ShellSurface::BrightnessCard);
                break;
            case GestureIntent::QuickSettings:
                result = show_surface(ShellSurface::QuickSettings);
                break;
            case GestureIntent::Launcher:
                result = show_surface(ShellSurface::Launcher);
                break;
            case GestureIntent::Back:
                if (host_.back) {
                    host_.back();
                }
                break;
            case GestureIntent::None:
            case GestureIntent::Consume:
                break;
            case GestureIntent::LeftCardIn:
                result = host_.card_step ? host_.card_step(true, true) : show_watch_face();
                break;
            case GestureIntent::RightCardIn:
                result = host_.card_step ? host_.card_step(false, true) : show_watch_face();
                break;
            }
            if (!result) {
                ESP_LOGW(SHELL_TAG, "Failed to handle navigation gesture: %s", result.error().c_str());
            }
        }
        const bool display_on = !host_.display_on || host_.display_on();
        if (display_on && !screen_timeout_latched_ && SCREEN_TIMEOUT_US > 0 &&
                esp_timer_get_time() - last_activity_us_ >= SCREEN_TIMEOUT_US) {
            screen_timeout_latched_ = true;
            if (host_.screen_timeout) {
                host_.screen_timeout();
            }
        }
        return {};
    }
    if (timer_id == status_timer_id_ && name == STATUS_TIMER) {
        refresh_status();
    }
    return {};
}

} // namespace espocket
