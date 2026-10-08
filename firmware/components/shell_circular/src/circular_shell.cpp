#include "shell_internal.hpp"
#include "brookesia/lib_utils/function_guard.hpp"
#include "pointer_click_filter.hpp"

namespace espocket {

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
    if (quick_settings_cleanup_pending_) return std::unexpected("Previous Quick Settings cleanup pending");
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
    const bool quick_action = action == OPEN_SETTINGS_QUICK_ACTION ||
        action == STEP_BRIGHTNESS_QUICK_ACTION || action == TOGGLE_WIFI_ACTION ||
        action == TOGGLE_DEVELOPER_MODE_ACTION;
    if (quick_action && !quick_settings_open()) return {}; // Retired overlay cannot change settings.
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


} // namespace espocket
