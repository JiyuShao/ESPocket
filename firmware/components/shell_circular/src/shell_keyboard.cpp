#include "shell_internal.hpp"

namespace espocket {

std::expected<void, std::string> CircularShell::show_keyboard(
    esp_brookesia::system::core::AppId app_id,
    esp_brookesia::system::core::KeyboardRequestId request_id,
    const esp_brookesia::system::core::KeyboardRequestOptions &options
)
{
    if (context_ == nullptr || !keyboard_state_) {
        return std::unexpected("Circular Shell is not running");
    }
    if (std::ranges::find(KEYBOARD_MODES, options.mode) == KEYBOARD_MODES.end()) {
        return std::unexpected("Unsupported keyboard mode: " + options.mode);
    }
    if (!supports_keyboard_modes(options.allowed_modes)) {
        return std::unexpected("Restricted keyboard mode sets are not supported");
    }
    if (options.max_length < 0) {
        return std::unexpected("Keyboard max_length must not be negative");
    }

    if (keyboard_state_ && host_.keyboard_valid) {
        esp_brookesia::system::core::AppId owner;
        esp_brookesia::system::core::KeyboardRequestId previous;
        {
            std::lock_guard lock(keyboard_state_->mutex);
            owner = keyboard_state_->app_id; previous = keyboard_state_->request_id;
        }
        if (previous != esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID &&
                !host_.keyboard_valid(owner, previous)) hide_keyboard(owner, previous);
    }
    LvglLock lvgl_lock;
    if (!lvgl_lock) {
        return std::unexpected("Failed to lock LVGL for keyboard");
    }

    std::lock_guard state_lock(keyboard_state_->mutex);
    if (keyboard_state_->request_id !=
            esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID) {
        if (!keyboard_state_->invalidated) return std::unexpected("Another keyboard request is already active");
        if (keyboard_state_->overlay) lv_obj_delete(keyboard_state_->overlay);
        keyboard_state_->overlay = nullptr;
        keyboard_state_->text_area = nullptr;
    }

    auto *overlay = lv_obj_create(lv_layer_top());
    if (overlay == nullptr) {
        return std::unexpected("Failed to create keyboard overlay");
    }
    lv_obj_remove_flag(overlay, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_size(overlay, lv_pct(100), lv_pct(100));
    lv_obj_center(overlay);
    lv_obj_set_style_bg_color(overlay, lv_color_hex(theme_color("bg.base")), 0);
    lv_obj_set_style_bg_opa(overlay, LV_OPA_COVER, 0);
    lv_obj_set_style_border_width(overlay, 0, 0);
    lv_obj_set_style_radius(overlay, 0, 0);
    lv_obj_set_style_pad_all(overlay, 0, 0);

    auto *title = lv_label_create(overlay);
    auto *text_area = lv_textarea_create(overlay);
    auto *keyboard = lv_keyboard_create(overlay);
    if (title == nullptr || text_area == nullptr || keyboard == nullptr) {
        lv_obj_delete(overlay);
        return std::unexpected("Failed to create keyboard controls");
    }

    lv_label_set_text(title, options.title.empty() ? "Enter text" : options.title.c_str());
    lv_label_set_long_mode(title, LV_LABEL_LONG_MODE_DOTS);
    lv_obj_set_size(title, 330, 28);
    lv_obj_align(title, LV_ALIGN_TOP_MID, 0, 52);
    lv_obj_set_style_text_color(title, lv_color_hex(theme_color("text.default")), 0);
    lv_obj_set_style_text_font(title, &lv_font_montserrat_20, 0);
    lv_obj_set_style_text_align(title, LV_TEXT_ALIGN_CENTER, 0);

    lv_textarea_set_one_line(text_area, true);
    lv_textarea_set_password_mode(text_area, options.password);
    if (options.password) {
        lv_textarea_set_password_show_time(text_area, 0);
    }
    if (options.max_length > 0) {
        lv_textarea_set_max_length(text_area, static_cast<uint32_t>(options.max_length));
    }
    lv_textarea_set_text(text_area, options.initial_text.c_str());
    lv_textarea_set_placeholder_text(text_area, options.placeholder.c_str());
    lv_obj_set_size(text_area, 330, 54);
    lv_obj_align(text_area, LV_ALIGN_TOP_MID, 0, 94);
    lv_obj_set_style_bg_color(text_area, lv_color_hex(theme_color("surface.raised")), 0);
    lv_obj_set_style_bg_opa(text_area, LV_OPA_COVER, 0);
    lv_obj_set_style_border_color(text_area, lv_color_hex(theme_color("border.default")), 0);
    lv_obj_set_style_border_width(text_area, 2, 0);
    lv_obj_set_style_radius(text_area, 16, 0);
    lv_obj_set_style_text_color(text_area, lv_color_hex(theme_color("text.default")), 0);
    lv_obj_set_style_text_color(
        text_area,
        lv_color_hex(theme_color("text.subtle")),
        LV_PART_TEXTAREA_PLACEHOLDER
    );
    lv_obj_set_style_text_font(text_area, &lv_font_montserrat_20, 0);

    lv_keyboard_set_textarea(keyboard, text_area);
    lv_keyboard_set_mode(keyboard, keyboard_mode(options.mode));
    lv_keyboard_set_popovers(keyboard, false);
    lv_obj_set_size(keyboard, 330, 220);
    lv_obj_align(keyboard, LV_ALIGN_BOTTOM_MID, 0, -68);
    lv_obj_set_style_bg_color(keyboard, lv_color_hex(theme_color("surface.raised")), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(keyboard, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_bg_color(keyboard, lv_color_hex(theme_color("surface.muted")), LV_PART_ITEMS);
    lv_obj_set_style_bg_color(
        keyboard,
        lv_color_hex(theme_color("primary.fill")),
        static_cast<lv_style_selector_t>(
            static_cast<uint32_t>(LV_PART_ITEMS) |
            static_cast<uint32_t>(LV_STATE_PRESSED)
        )
    );
    lv_obj_set_style_text_color(keyboard, lv_color_hex(theme_color("text.default")), LV_PART_ITEMS);
    lv_obj_set_style_text_color(
        keyboard,
        lv_color_hex(theme_color("primary.on")),
        static_cast<lv_style_selector_t>(
            static_cast<uint32_t>(LV_PART_ITEMS) |
            static_cast<uint32_t>(LV_STATE_PRESSED)
        )
    );
    lv_obj_set_style_text_font(keyboard, &lv_font_montserrat_18, LV_PART_ITEMS);
    lv_obj_set_style_radius(keyboard, 8, LV_PART_ITEMS);

    retain_overlay_userdata(overlay, keyboard_state_);
    keyboard_state_->app_id = app_id;
    keyboard_state_->request_id = request_id;
    keyboard_state_->overlay = overlay;
    keyboard_state_->text_area = text_area;
    keyboard_state_->result_pending = false;
    keyboard_state_->confirmed = false;
    keyboard_state_->invalidated = false;
    keyboard_state_->text.clear();

    auto keyboard_event = [](lv_event_t *event) {
        auto *state = static_cast<KeyboardState *>(lv_event_get_user_data(event));
        if (state == nullptr) {
            return;
        }
        std::lock_guard lock(state->mutex);
        if (state->request_id ==
                esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID ||
                state->result_pending || state->suspended || state->invalidated) {
            return;
        }
        state->confirmed = lv_event_get_code(event) == LV_EVENT_READY;
        state->text = state->confirmed && state->text_area != nullptr ?
                      lv_textarea_get_text(state->text_area) : "";
        state->result_pending = true;
    };
    lv_obj_add_event_cb(keyboard, keyboard_event, LV_EVENT_READY, keyboard_state_.get());
    lv_obj_add_event_cb(keyboard, keyboard_event, LV_EVENT_CANCEL, keyboard_state_.get());
    lv_obj_add_state(text_area, LV_STATE_FOCUSED);

    keyboard_state_->suspended = home_gesture_state_ && home_gesture_state_->modal_active.load();
    if (keyboard_state_->suspended) lv_obj_add_flag(overlay, LV_OBJ_FLAG_HIDDEN);
    if (home_gesture_state_) home_gesture_state_->keyboard_active.store(true, std::memory_order_release);
    if (home_gesture_state_) reset_shell_gesture(*home_gesture_state_, true);
    ESP_LOGI(SHELL_TAG, "System keyboard opened");
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

std::expected<void, std::string> CircularShell::show_loading(esp_brookesia::system::core::AppId app_id, bool startup)
{
    if (!context_ || !loading_state_) return std::unexpected("Circular Shell is unavailable");
    LvglLock gui_lock;
    if (!gui_lock) return std::unexpected("Failed to lock LVGL for Loading");
    std::lock_guard state_lock(loading_state_->mutex);
    if (loading_state_->overlay) {
        if (loading_state_->app_id == app_id && !loading_state_->invalidated) {
            (startup ? loading_state_->startup : loading_state_->app_wait) = true;
            return {};
        }
        return std::unexpected("Another Loading owner is active");
    }
    auto *overlay = lv_label_create(lv_layer_top());
    if (!overlay) return std::unexpected("Failed to create Loading feedback");
    lv_label_set_text(overlay, "Loading...");
    lv_obj_set_style_text_font(overlay, &lv_font_montserrat_20, 0);
    lv_obj_set_style_text_color(overlay, lv_color_hex(theme_color("text.default")), 0);
    lv_obj_align(overlay, LV_ALIGN_BOTTOM_MID, 0, -42);
    lv_obj_remove_flag(overlay, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_move_to_index(overlay, 0); // Feedback never takes input or obscures Keyboard/Dialog.
    (startup ? loading_state_->startup : loading_state_->app_wait) = true;
    loading_state_->app_id = app_id;
    loading_state_->overlay = overlay;
    loading_state_->invalidated = false;
    return {};
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

void CircularShell::suspend_keyboard_input(bool suspend)
{
    // Caller holds LVGL before entering either Overlay state mutex.
    if (!keyboard_state_) return;
    std::lock_guard lock(keyboard_state_->mutex);
    keyboard_state_->suspended = true; // Resume only after the Owner tick validates the request.
    if (!keyboard_state_->overlay) return;
    if (suspend || keyboard_state_->invalidated) lv_obj_add_flag(keyboard_state_->overlay, LV_OBJ_FLAG_HIDDEN);
    // A closed Dialog leaves the keyboard hidden until refresh_overlay_input.
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

void CircularShell::refresh_overlay_input()
{
    if (message_dialog_state_ && host_.message_dialog_valid) {
        esp_brookesia::system::core::AppId owner;
        esp_brookesia::system::core::MessageDialogRequestId request;
        {
            std::lock_guard lock(message_dialog_state_->mutex);
            owner = message_dialog_state_->app_id; request = message_dialog_state_->request_id;
        }
        if (request != esp_brookesia::system::core::INVALID_MESSAGE_DIALOG_REQUEST_ID &&
                !host_.message_dialog_valid(owner, request)) hide_message_dialog(owner, request);
    }
    if (!keyboard_state_) return;
    esp_brookesia::system::core::AppId owner;
    esp_brookesia::system::core::KeyboardRequestId request;
    {
        std::lock_guard lock(keyboard_state_->mutex);
        owner = keyboard_state_->app_id; request = keyboard_state_->request_id;
    }
    if (request == esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID) return;
    if (host_.keyboard_valid && !host_.keyboard_valid(owner, request)) {
        hide_keyboard(owner, request);
        return;
    }
    LvglLock gui_lock;
    if (!gui_lock) return;
    std::lock_guard lock(keyboard_state_->mutex);
    if (keyboard_state_->request_id != request || keyboard_state_->app_id != owner ||
            keyboard_state_->invalidated || (home_gesture_state_ && home_gesture_state_->modal_active.load())) return;
    keyboard_state_->suspended = false;
    if (keyboard_state_->overlay) lv_obj_remove_flag(keyboard_state_->overlay, LV_OBJ_FLAG_HIDDEN);
}

void CircularShell::poll_keyboard()
{
        if (keyboard_state_ && host_.keyboard_result) {
            esp_brookesia::system::core::AppId app_id =
                esp_brookesia::system::core::INVALID_APP_ID;
            esp_brookesia::system::core::KeyboardRequestId request_id =
                esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID;
            bool confirmed = false;
            std::string text;
            {
                std::lock_guard lock(keyboard_state_->mutex);
                if (keyboard_state_->result_pending && !keyboard_state_->suspended &&
                        (!host_.display_on || host_.display_on()) && !keyboard_state_->invalidated) {
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

} // namespace espocket
