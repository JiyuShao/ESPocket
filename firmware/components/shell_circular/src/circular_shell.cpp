#include "shell_internal.hpp"
#include "brookesia/lib_utils/function_guard.hpp"
#include "pointer_click_filter.hpp"

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
    if (pointer_click_filters_) return std::unexpected("Previous pointer filter cleanup pending");
    // A failed stop retains revoked presentation storage until GUI cleanup.
    // Never overwrite it with a new Running Instance's state.
    if (loading_state_) {
        std::lock_guard lock(loading_state_->mutex);
        if (loading_state_->overlay) return std::unexpected("Previous Loading cleanup pending");
    }
    if (keyboard_state_) {
        std::lock_guard lock(keyboard_state_->mutex);
        if (keyboard_state_->overlay) return std::unexpected("Previous keyboard cleanup pending");
    }
    if (message_dialog_state_) {
        std::lock_guard lock(message_dialog_state_->mutex);
        if (message_dialog_state_->overlay) return std::unexpected("Previous Dialog cleanup pending");
    }
    if (back_overlay_state_ && (back_overlay_state_->button || back_overlay_state_->card_hint)) {
        return std::unexpected("Previous Back cleanup pending");
    }
    context_ = &context;
    // Core does not call Native on_stop when on_start fails.
    esp_brookesia::lib_utils::FunctionGuard start_cleanup([this, &context]() {
        gesture_connection_.disconnect();
        if (pointer_click_filters_) {
            LvglLock lock;
            if (lock) {
                pointer_click_filters_->remove();
                pointer_click_filters_.reset();
            }
        }
        if (home_intent_timer_id_ != esp_brookesia::system::core::INVALID_TIMER_ID) {
            (void)context.timer().stop(home_intent_timer_id_);
        }
        home_intent_timer_id_ = esp_brookesia::system::core::INVALID_TIMER_ID;
        display_binding_.release();
        if (!pointer_click_filters_) home_gesture_state_.reset();
        loading_state_.reset();
        keyboard_state_.reset();
        message_dialog_state_.reset();
        back_overlay_state_.reset();
        context_ = nullptr;
    });
    if (auto colors = load_theme_colors(); !colors) {
        return colors;
    }
    loading_state_ = std::make_shared<LoadingState>();
    keyboard_state_ = std::make_shared<KeyboardState>();
    message_dialog_state_ = std::make_shared<MessageDialogState>();
    back_overlay_state_ = std::make_shared<BackOverlayState>();

    for (const auto action : {
             OPEN_HELLO_NATIVE_ACTION,
             OPEN_HELLO_RUNTIME_ACTION,
             OPEN_SETTINGS_ACTION,
             OPEN_SETTINGS_CARD_ACTION,
             OPEN_SETTINGS_QUICK_ACTION,
             OPEN_APP_STORE_ACTION,
             OPEN_DYNAMIC_APP_ACTION,
             STEP_BRIGHTNESS_ACTION,
             STEP_BRIGHTNESS_QUICK_ACTION,
             TOGGLE_WIFI_ACTION,
             TOGGLE_DEVELOPER_MODE_ACTION,
         }) {
        auto action_result = context.gui().subscribe_action(action);
        if (!action_result) {
            return std::unexpected("Failed to subscribe Launcher action: " + action_result.error());
        }
    }

    home_gesture_state_ = std::make_shared<HomeGestureState>();
    last_activity_generation_ = 0;
    last_activity_us_ = esp_timer_get_time();
    screen_timeout_latched_ = false;
    auto home_timer = context.timer().start_periodic(
                          HOME_INTENT_TIMER,
                          HOME_INTENT_INTERVAL_MS
                      );
    if (!home_timer) {
        return std::unexpected(
            "Failed to start Home intent timer: " + home_timer.error()
        );
    }
    home_intent_timer_id_ = *home_timer;
    auto gesture_result = configure_home_gesture();
    if (!gesture_result) {
        return gesture_result;
    }

    callback_state_ = std::make_shared<CallbackState>();
    callback_state_->owner = this;
    launcher_connection_ = context.gui().subscribe_action(OPEN_DYNAMIC_APP_ACTION,
        [state = callback_state_](const esp_brookesia::gui::Event &event) {
            std::lock_guard lock(state->mutex);
            if (!state->owner) return;
            std::lock_guard intent_lock(state->owner->launcher_intent_mutex_);
            // Remember the exact immutable view path; retired views cannot launch.
            if (state->owner->launcher_intent_.empty()) state->owner->launcher_intent_ = event.path;
        });
    launcher_generation_ = UINT64_MAX;
    launcher_refresh_at_us_ = 0;
    refresh_launcher();
    start_status();
    start_cleanup.release();
    ESP_LOGI(SHELL_TAG, "Circular Shell started");
    return {};
}

std::expected<void, std::string> CircularShell::on_stop(
    esp_brookesia::system::core::AppContext &context
)
{
    (void)context;
    if (pointer_click_filters_) {
        LvglLock lock;
        if (!lock) return std::unexpected("Unable to remove pointer click filter");
        pointer_click_filters_->remove();
        pointer_click_filters_.reset();
    }
    stop_launcher();
    bool overlay_cleanup_pending = false;
    if (loading_state_) {
        esp_brookesia::system::core::AppId app;
        { std::lock_guard lock(loading_state_->mutex); app = loading_state_->app_id; }
        hide_loading(app, true);
        hide_loading(app);
        std::lock_guard lock(loading_state_->mutex);
        overlay_cleanup_pending |= loading_state_->overlay != nullptr;
    }
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
    if (message_dialog_state_) {
        esp_brookesia::system::core::AppId app_id;
        esp_brookesia::system::core::MessageDialogRequestId request_id;
        {
            std::lock_guard lock(message_dialog_state_->mutex);
            app_id = message_dialog_state_->app_id;
            request_id = message_dialog_state_->request_id;
        }
        hide_message_dialog(app_id, request_id);
    }
    if (keyboard_state_) {
        std::lock_guard lock(keyboard_state_->mutex);
        overlay_cleanup_pending |= keyboard_state_->overlay != nullptr;
    }
    if (message_dialog_state_) {
        std::lock_guard lock(message_dialog_state_->mutex);
        overlay_cleanup_pending |= message_dialog_state_->overlay != nullptr;
    }
    sync_default_back(false);
    sync_card_hint(false);
    if (back_overlay_state_ && (back_overlay_state_->button || back_overlay_state_->card_hint)) {
        overlay_cleanup_pending = true;
    }
    gesture_connection_.disconnect();
    if (home_intent_timer_id_ != esp_brookesia::system::core::INVALID_TIMER_ID) {
        (void)context.timer().stop(home_intent_timer_id_);
    }
    home_intent_timer_id_ = esp_brookesia::system::core::INVALID_TIMER_ID;
    home_gesture_state_.reset();
    stop_status();
    display_binding_.release();
    context_ = nullptr;
    if (overlay_cleanup_pending) {
        // All input/subscriptions/bindings are already stopped, even on GUI failure.
        // Keep identities revoked and report incomplete resource cleanup.
        return std::unexpected("Shell Overlay GUI cleanup pending");
    }
    keyboard_state_.reset();
    message_dialog_state_.reset();
    loading_state_.reset();
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
    // GUI actions are queued. A released pull may navigate Home before the
    // clicked row reaches this callback; reject actions from the old Launcher.
    const bool launcher_action = action == OPEN_HELLO_NATIVE_ACTION ||
        action == OPEN_HELLO_RUNTIME_ACTION || action == OPEN_SETTINGS_ACTION ||
        action == OPEN_APP_STORE_ACTION;
    if (launcher_action && (current_surface() != ShellSurface::Launcher ||
            (host_.app_visible && host_.app_visible()) ||
            (home_gesture_state_ && home_gesture_state_->modal_active.load(std::memory_order_acquire)))) {
        return {};
    }
    // A completed pull also suppresses the row while Launcher is still active.
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
    if (action == OPEN_DYNAMIC_APP_ACTION) { return {}; } // Event path is dispatched on the Owner tick.
    if (action == STEP_BRIGHTNESS_ACTION || action == STEP_BRIGHTNESS_QUICK_ACTION) {
        auto result = step_brightness();
        if (!result) {
            set_status_text(BRIGHTNESS_CARD_PATH, "Brightness: unavailable");
            set_status_text(QUICK_BRIGHTNESS_PATH, "Unavailable");
        }
        return result;
    }
    if (action == TOGGLE_WIFI_ACTION) {
        auto result = toggle_wifi();
        if (!result) {
            set_status_text(QUICK_WIFI_PATH, "Unavailable");
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
        // Consume recognized PWR before any not-yet-submitted GUI intent.
        if (host_.tick) host_.tick();
        refresh_overlay_input();
        if (loading_state_) {
            esp_brookesia::system::core::AppId app;
            bool retry;
            { std::lock_guard lock(loading_state_->mutex); app = loading_state_->app_id; retry = loading_state_->invalidated; }
            if (retry) hide_loading(app);
        }
        if (keyboard_state_) {
            esp_brookesia::system::core::AppId app;
            esp_brookesia::system::core::KeyboardRequestId request;
            bool retry;
            {
                std::lock_guard lock(keyboard_state_->mutex);
                app = keyboard_state_->app_id; request = keyboard_state_->request_id;
                retry = keyboard_state_->invalidated;
            }
            if (retry) hide_keyboard(app, request);
        }
        if (message_dialog_state_) {
            esp_brookesia::system::core::AppId app;
            esp_brookesia::system::core::MessageDialogRequestId request;
            bool retry;
            {
                std::lock_guard lock(message_dialog_state_->mutex);
                app = message_dialog_state_->app_id; request = message_dialog_state_->request_id;
                retry = message_dialog_state_->invalidated;
            }
            if (retry) hide_message_dialog(app, request);
        }
        if (host_.expire_back) {
            host_.expire_back();
        }
        if (back_overlay_state_) {
            const bool clicked = back_overlay_state_->clicked.exchange(
                                     false, std::memory_order_acq_rel
                                 );
            if (clicked && !(home_gesture_state_ && home_gesture_state_->modal_active.load()) &&
                    !cancel_keyboard_input() && host_.back) {
                host_.back();
            }
            bool keyboard_active = false;
            if (keyboard_state_) {
                std::lock_guard lock(keyboard_state_->mutex);
                keyboard_active = keyboard_state_->request_id !=
                                  esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID;
            }
            const bool modal_active = home_gesture_state_ &&
                home_gesture_state_->modal_active.load(std::memory_order_acquire);
            const bool visible = (keyboard_active || (host_.back_ui && host_.back_ui().default_visible)) &&
                                 !modal_active;
            sync_default_back(visible);
            const auto surface = current_surface();
            sync_card_hint(!keyboard_active && !modal_active && !(host_.app_visible && host_.app_visible()) &&
                (surface == ShellSurface::LeftAppCard || surface == ShellSurface::RightAppCard));
        }
        poll_keyboard();
        poll_message_dialog();

        refresh_launcher();
        if (status_refresh_deferred_) refresh_status();
        dispatch_launcher();
        if (home_gesture_state_) {
            const auto activity = home_gesture_state_->activity_generation.load(std::memory_order_acquire);
            if (activity != last_activity_generation_) {
                last_activity_generation_ = activity;
                last_activity_us_ = esp_timer_get_time();
                screen_timeout_latched_ = false;
            }
            if (current_surface() == ShellSurface::Launcher &&
                    (!host_.app_visible || !host_.app_visible())) {
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
                        visual == 2 ? LV_SYMBOL_DOWN "  Release for Home" :
                        visual == 1 ? LV_SYMBOL_DOWN "  Keep pulling" :
                        launcher_page_ == 0 ? "Swipe up | Home down" : "Swipe up / down"
                    );
                }
            }
            const auto intent = static_cast<GestureIntent>(
                                    home_gesture_state_->pending_gesture.exchange(
                                        static_cast<uint8_t>(GestureIntent::None),
                                        std::memory_order_acq_rel
                                    )
                                );
            const bool cancel_pointer = home_gesture_state_->pointer_cancel_pending.exchange(
                false, std::memory_order_acq_rel);
            if (cancel_pointer || intent != GestureIntent::None) {
                LvglLock lock;
                if (!lock) return std::unexpected("Unable to consume navigation touch");
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
            case GestureIntent::LauncherNext:
                result = show_launcher_page(launcher_page_ + 1);
                break;
            case GestureIntent::LauncherPrevious:
                result = show_launcher_page(launcher_page_ == 0 ? 0 : launcher_page_ - 1);
                break;
            case GestureIntent::Back:
                if (!cancel_keyboard_input() && host_.back) {
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
