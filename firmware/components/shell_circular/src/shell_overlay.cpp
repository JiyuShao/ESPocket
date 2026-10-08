#include "shell_overlay_internal.hpp"
#include "pointer_click_filter.hpp"

namespace espocket {

CircularShell::CircularShell(
    uint32_t display_output_id,
    ShellHost host
)
    : display_output_id_(display_output_id),
      host_(std::move(host))
{}

std::expected<void, std::string> CircularShell::show_surface(ShellSurface surface)
{
    if (context_ == nullptr) {
        return std::unexpected("Circular Shell is not running");
    }
    if (surface == ShellSurface::QuickSettings) {
        if (quick_settings_open()) return {};
        if (host_.display_on && !host_.display_on()) return std::unexpected("Display is off");
        if (host_.quick_settings_display) {
            auto acquired = host_.quick_settings_display(true, false);
            if (!acquired) return acquired;
        }
        auto opened = context_->gui().trigger_screen_flow("quick_settings_flow", "open_quick_settings");
        if (!opened) {
            if (host_.quick_settings_display) (void)host_.quick_settings_display(false, true);
            return opened;
        }
        quick_settings_return_surface_ = current_surface();
        home_gesture_state_->surface.store(ShellSurface::QuickSettings, std::memory_order_release);
        home_gesture_state_->activity_generation.fetch_add(1, std::memory_order_acq_rel);
        refresh_overlay_input();
        sync_default_back(false);
        sync_card_hint(false);
        refresh_status();
        return {};
    }
    if (quick_settings_open()) {
        auto closed = dismiss_quick_settings(false);
        if (!closed) return closed;
    }
    std::string_view action;
    switch (surface) {
    case ShellSurface::WatchFace: action = "open_watch_face"; break;
    case ShellSurface::BatteryCard: action = "open_battery_card"; break;
    case ShellSurface::BrightnessCard: action = "open_brightness_card"; break;
    case ShellSurface::QuickSettings: action = "open_quick_settings"; break;
    case ShellSurface::Launcher: action = "open_launcher"; break;
    case ShellSurface::LeftAppCard:
    case ShellSurface::RightAppCard: action = "open_app_card"; break;
    }
    auto result = context_->gui().trigger_screen_flow(PAGE_FLOW, action);
    if (result && home_gesture_state_) {
        home_gesture_state_->surface.store(surface, std::memory_order_release);
        home_gesture_state_->activity_generation.fetch_add(1, std::memory_order_acq_rel);
        if (surface == ShellSurface::Launcher) {
            home_gesture_state_->launcher_pull_distance.store(0, std::memory_order_release);
            result = show_launcher_page(0);
        } else {
            home_gesture_state_->launcher_pull_distance.store(0, std::memory_order_release);
        }
    }
    if (result && host_.surface_changed) host_.surface_changed(surface);
    if (result) sync_card_hint(surface == ShellSurface::LeftAppCard || surface == ShellSurface::RightAppCard);
    return result;
}

ShellSurface CircularShell::current_surface() const
{
    return home_gesture_state_ ?
           home_gesture_state_->surface.load(std::memory_order_acquire) :
           ShellSurface::WatchFace;
}

bool CircularShell::quick_settings_open() const
{
    return current_surface() == ShellSurface::QuickSettings;
}

ShellSurface CircularShell::underlying_surface() const
{
    return quick_settings_open() ? quick_settings_return_surface_ : current_surface();
}

std::expected<void, std::string> CircularShell::dismiss_quick_settings(bool restore_display)
{
    if (!quick_settings_open()) return {};
    auto closed = context_->gui().trigger_screen_flow("quick_settings_flow", "close_quick_settings");
    if (!closed) return closed;
    home_gesture_state_->surface.store(quick_settings_return_surface_, std::memory_order_release);
    home_gesture_state_->activity_generation.fetch_add(1, std::memory_order_acq_rel);
    refresh_overlay_input(); // Core validates identities before resuming any keyboard/dialog.
    if (host_.quick_settings_display) return host_.quick_settings_display(false, restore_display);
    return {};
}

std::expected<void, std::string> CircularShell::set_display_on(bool on)
{
    LvglLock lock;
    if (!lock) {
        return std::unexpected("Failed to lock LVGL while changing display input state");
    }
    for (auto *input = lv_indev_get_next(nullptr); input != nullptr; input = lv_indev_get_next(input)) {
        if (lv_indev_get_type(input) == LV_INDEV_TYPE_POINTER) {
            lv_indev_enable(input, on);
        }
    }
    if (message_dialog_state_) {
        std::lock_guard state_lock(message_dialog_state_->mutex);
        const auto now = esp_timer_get_time();
        if (!on && message_dialog_state_->paused_at_us < 0) message_dialog_state_->paused_at_us = now;
        if (on && message_dialog_state_->paused_at_us >= 0) {
            if (message_dialog_state_->deadline_us) {
                message_dialog_state_->deadline_us += now - message_dialog_state_->paused_at_us;
            }
            message_dialog_state_->paused_at_us = -1;
        }
    }
    if (on) {
        last_activity_us_ = esp_timer_get_time();
        screen_timeout_latched_ = false;
    }
    return {};
}

void CircularShell::hide_keyboard(
    esp_brookesia::system::core::AppId app_id,
    esp_brookesia::system::core::KeyboardRequestId request_id
)
{
    if (!keyboard_state_) {
        return;
    }

    {
        std::lock_guard state_lock(keyboard_state_->mutex);
        if (keyboard_state_->app_id != app_id || keyboard_state_->request_id != request_id) return;
        keyboard_state_->invalidated = true;
    }
    LvglLock lvgl_lock;
    if (!lvgl_lock) {
        ESP_LOGW(SHELL_TAG, "Failed to lock LVGL while hiding keyboard");
        return;
    }

    std::lock_guard state_lock(keyboard_state_->mutex);
    if (keyboard_state_->app_id != app_id || keyboard_state_->request_id != request_id) {
        return;
    }
    if (keyboard_state_->overlay != nullptr && lv_obj_is_valid(keyboard_state_->overlay)) {
        lv_obj_delete(keyboard_state_->overlay);
    }
    keyboard_state_->app_id = esp_brookesia::system::core::INVALID_APP_ID;
    keyboard_state_->request_id =
        esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID;
    keyboard_state_->overlay = nullptr;
    keyboard_state_->text_area = nullptr;
    keyboard_state_->result_pending = false;
    keyboard_state_->confirmed = false;
    keyboard_state_->invalidated = false;
    keyboard_state_->text.clear();
    if (home_gesture_state_) home_gesture_state_->keyboard_active.store(false, std::memory_order_release);
    ESP_LOGI(SHELL_TAG, "System keyboard closed");
}

void CircularShell::hide_loading(esp_brookesia::system::core::AppId app_id, bool startup)
{
    if (!loading_state_) return;
    {
        std::lock_guard state_lock(loading_state_->mutex);
        if (loading_state_->app_id != app_id || !loading_state_->overlay) return;
        (startup ? loading_state_->startup : loading_state_->app_wait) = false;
        if (loading_state_->startup || loading_state_->app_wait) return;
        loading_state_->invalidated = true;
    }
    LvglLock gui_lock;
    if (!gui_lock) return; // Retry on the Owner tick; no active request can be resurrected.
    std::lock_guard state_lock(loading_state_->mutex);
    if (loading_state_->app_id != app_id) return;
    if (loading_state_->overlay) lv_obj_delete(loading_state_->overlay);
    loading_state_->overlay = nullptr;
    loading_state_->app_id = esp_brookesia::system::core::INVALID_APP_ID;
    loading_state_->invalidated = false;
}

bool CircularShell::cancel_keyboard_input()
{
    if (!keyboard_state_) return false;
    std::lock_guard lock(keyboard_state_->mutex);
    if (keyboard_state_->request_id == esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID) return false;
    if (!keyboard_state_->suspended && !keyboard_state_->invalidated) {
        keyboard_state_->confirmed = false;
        keyboard_state_->text.clear();
        keyboard_state_->result_pending = true;
    }
    return true; // Never fall through to the underlying App Page.
}

void CircularShell::discard_overlay_choices()
{
    cancel_gesture_input();
    if (back_overlay_state_) back_overlay_state_->clicked.store(false, std::memory_order_release);
    if (keyboard_state_) {
        std::lock_guard lock(keyboard_state_->mutex);
        keyboard_state_->result_pending = false;
        keyboard_state_->text.clear();
    }
    if (message_dialog_state_) {
        std::lock_guard lock(message_dialog_state_->mutex);
        message_dialog_state_->result_pending = false;
    }
}

bool CircularShell::refresh_overlay_input()
{
    // Core calls never run under GUI/state locks. Re-check identity before mutation.
    if (message_dialog_state_ && host_.message_dialog_valid) {
        esp_brookesia::system::core::AppId app;
        esp_brookesia::system::core::MessageDialogRequestId request;
        { std::lock_guard lock(message_dialog_state_->mutex);
          app = message_dialog_state_->app_id; request = message_dialog_state_->request_id; }
        if (request != esp_brookesia::system::core::INVALID_MESSAGE_DIALOG_REQUEST_ID &&
                !host_.message_dialog_valid(app, request)) hide_message_dialog(app, request);
    }
    if (keyboard_state_ && host_.keyboard_valid) {
        esp_brookesia::system::core::AppId app;
        esp_brookesia::system::core::KeyboardRequestId request;
        { std::lock_guard lock(keyboard_state_->mutex);
          app = keyboard_state_->app_id; request = keyboard_state_->request_id; }
        if (request != esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID &&
                !host_.keyboard_valid(app, request)) hide_keyboard(app, request);
    }
    const bool covered = quick_settings_open();
    bool dialog_present = false, keyboard_present = false, changed = false;
    if (message_dialog_state_) {
        std::lock_guard lock(message_dialog_state_->mutex);
        dialog_present = message_dialog_state_->overlay != nullptr;
        changed = dialog_present && message_dialog_state_->suspended !=
            (covered || message_dialog_state_->invalidated);
    }
    if (keyboard_state_) {
        std::lock_guard lock(keyboard_state_->mutex);
        keyboard_present = keyboard_state_->overlay != nullptr;
        changed = changed || (keyboard_present && keyboard_state_->suspended !=
            (covered || dialog_present || keyboard_state_->invalidated));
    }
    // GUI first, then state. A revoked Dialog awaiting deletion still blocks
    // lower input. Stable presentation does not acquire GUI every 50 ms tick.
    if (changed) {
        LvglLock gui_lock;
        if (!gui_lock) return false;
        if (message_dialog_state_) {
            std::lock_guard lock(message_dialog_state_->mutex);
            message_dialog_state_->suspended = covered || message_dialog_state_->invalidated;
            if (message_dialog_state_->overlay) {
                if (message_dialog_state_->suspended) lv_obj_add_flag(message_dialog_state_->overlay, LV_OBJ_FLAG_HIDDEN);
                else lv_obj_remove_flag(message_dialog_state_->overlay, LV_OBJ_FLAG_HIDDEN);
            }
        }
        if (keyboard_state_) {
            std::lock_guard lock(keyboard_state_->mutex);
            keyboard_state_->suspended = covered || dialog_present || keyboard_state_->invalidated;
            if (keyboard_state_->overlay) {
                if (keyboard_state_->suspended) lv_obj_add_flag(keyboard_state_->overlay, LV_OBJ_FLAG_HIDDEN);
                else lv_obj_remove_flag(keyboard_state_->overlay, LV_OBJ_FLAG_HIDDEN);
            }
        }
    }
    if (home_gesture_state_) {
        home_gesture_state_->modal_active.store(dialog_present, std::memory_order_release);
        home_gesture_state_->keyboard_active.store(keyboard_present, std::memory_order_release);
    }
    return true;
}

void CircularShell::poll_keyboard()
{
    if (keyboard_state_ && host_.keyboard_result && (!host_.display_on || host_.display_on())) {
        esp_brookesia::system::core::AppId app_id =
            esp_brookesia::system::core::INVALID_APP_ID;
        esp_brookesia::system::core::KeyboardRequestId request_id =
            esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID;
        bool confirmed = false;
        std::string text;
        {
            std::lock_guard lock(keyboard_state_->mutex);
            if (keyboard_state_->result_pending && !keyboard_state_->suspended &&
                    !keyboard_state_->invalidated) {
                app_id = keyboard_state_->app_id;
                request_id = keyboard_state_->request_id;
                confirmed = keyboard_state_->confirmed;
                text = keyboard_state_->text;
            }
        }
        if (request_id != esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID) {
            hide_keyboard(app_id, request_id);
            bool hidden;
            {
                std::lock_guard lock(keyboard_state_->mutex);
                hidden = keyboard_state_->request_id != request_id;
                // A failed hide is still this unsubmitted result, not Core invalidation.
                if (!hidden) keyboard_state_->invalidated = false;
            }
            if (hidden) host_.keyboard_result(app_id, request_id, confirmed, std::move(text));
        }
    }
}

void CircularShell::hide_message_dialog(esp_brookesia::system::core::AppId app_id,
    esp_brookesia::system::core::MessageDialogRequestId request_id)
{
    if (!message_dialog_state_) return;
    {
        std::lock_guard state_lock(message_dialog_state_->mutex);
        if (message_dialog_state_->app_id != app_id || message_dialog_state_->request_id != request_id ||
                !message_dialog_state_->overlay) return;
        message_dialog_state_->invalidated = true;
    }
    LvglLock lock;
    if (!lock) { ESP_LOGW(SHELL_TAG, "Failed to lock LVGL for message dialog hide"); return; }
    std::lock_guard state_lock(message_dialog_state_->mutex);
    if (message_dialog_state_->app_id != app_id || message_dialog_state_->request_id != request_id) return;
    if (message_dialog_state_->overlay) lv_obj_delete(message_dialog_state_->overlay);
    message_dialog_state_->overlay = nullptr;
    message_dialog_state_->request_id = esp_brookesia::system::core::INVALID_MESSAGE_DIALOG_REQUEST_ID;
    message_dialog_state_->app_id = esp_brookesia::system::core::INVALID_APP_ID;
    message_dialog_state_->result_pending = false;
    message_dialog_state_->deadline_us = 0;
    message_dialog_state_->paused_at_us = -1;
    message_dialog_state_->invalidated = false;
    if (home_gesture_state_) home_gesture_state_->modal_active.store(false, std::memory_order_release);
    ESP_LOGI(SHELL_TAG, "System message dialog closed: request=%" PRIu64, request_id);
}

void CircularShell::poll_message_dialog()
{
    if (!message_dialog_state_ || !host_.message_dialog_result ||
            (host_.display_on && !host_.display_on())) return;
    esp_brookesia::system::core::AppId app_id;
    esp_brookesia::system::core::MessageDialogRequestId request_id;
    int32_t index;
    auto reason = esp_brookesia::system::core::MessageDialogCloseReason::Button;
    {
        std::lock_guard lock(message_dialog_state_->mutex);
        if (message_dialog_state_->request_id == esp_brookesia::system::core::INVALID_MESSAGE_DIALOG_REQUEST_ID) return;
        if (message_dialog_state_->invalidated) return;
        // A queued choice is not submitted while covered, but must not suppress
        // the original timeout. Closing the panel cannot revive an expired choice.
        if (!message_dialog_state_->result_pending || message_dialog_state_->suspended) {
            if (!message_dialog_state_->deadline_us || esp_timer_get_time() < message_dialog_state_->deadline_us) return;
            reason = esp_brookesia::system::core::MessageDialogCloseReason::Timeout;
        }
        app_id = message_dialog_state_->app_id;
        request_id = message_dialog_state_->request_id;
        index = reason == esp_brookesia::system::core::MessageDialogCloseReason::Button ? message_dialog_state_->button_index : -1;
    }
    // UI callbacks only record intent. Complete on the serialized App task, after releasing LVGL.
    hide_message_dialog(app_id, request_id);
    {
        std::lock_guard lock(message_dialog_state_->mutex);
        if (message_dialog_state_->request_id == request_id) {
            message_dialog_state_->invalidated = false;
            return; // Retry unsubmitted choice after failed GUI cleanup.
        }
    }
    host_.message_dialog_result(app_id, request_id, index, reason);
}

void CircularShell::prepare_overlay_input()
{
    refresh_overlay_input();
    if (loading_state_) {
        esp_brookesia::system::core::AppId app;
        bool retry;
        {
            std::lock_guard lock(loading_state_->mutex);
            app = loading_state_->app_id; retry = loading_state_->invalidated;
        }
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
}

void CircularShell::complete_overlay_input()
{
    // Navigation may have opened/closed QS since preparation. Validate and
    // reconcile before submitting intent, then reveal any newly unblocked input.
    if (!refresh_overlay_input()) return;
    poll_message_dialog();
    if (!refresh_overlay_input()) return;
    poll_keyboard();
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
        prepare_overlay_input();
        if (host_.expire_back) {
            host_.expire_back();
        }
        if (back_overlay_state_) {
            const bool clicked = back_overlay_state_->clicked.exchange(
                                     false, std::memory_order_acq_rel
                                 );
            if (clicked && !quick_settings_open() && !(home_gesture_state_ && home_gesture_state_->modal_active.load()) &&
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
                                 !modal_active && !quick_settings_open();
            sync_default_back(visible);
            const auto surface = current_surface();
            sync_card_hint(!quick_settings_open() && !keyboard_active && !modal_active && !(host_.app_visible && host_.app_visible()) &&
                (surface == ShellSurface::LeftAppCard || surface == ShellSurface::RightAppCard));
        }

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
            case GestureIntent::CloseQuickSettings:
                result = dismiss_quick_settings();
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
        complete_overlay_input();
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
    bool overlay_cleanup_pending = false;
    if (quick_settings_open() || quick_settings_cleanup_pending_) {
        auto closed = context.gui().trigger_screen_flow("quick_settings_flow", "close_quick_settings");
        quick_settings_cleanup_pending_ = !closed;
        overlay_cleanup_pending |= quick_settings_cleanup_pending_;
        if (host_.quick_settings_display) (void)host_.quick_settings_display(false, false);
    }
    stop_launcher();
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

} // namespace espocket
