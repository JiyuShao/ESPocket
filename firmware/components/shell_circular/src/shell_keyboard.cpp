#include "shell_overlay_internal.hpp"

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

    refresh_overlay_input();
    {
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

        keyboard_state_->suspended = true;
        lv_obj_add_flag(overlay, LV_OBJ_FLAG_HIDDEN);
        if (home_gesture_state_) reset_shell_gesture(*home_gesture_state_, true);
        ESP_LOGI(SHELL_TAG, "System keyboard opened");
    }
    refresh_overlay_input();
    return {};
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
    auto *overlay = lv_obj_create(lv_layer_top());
    if (!overlay) return std::unexpected("Failed to create Loading feedback");
    auto *spinner = lv_spinner_create(overlay);
    auto *label = lv_label_create(overlay);
    if (!spinner || !label) {
        lv_obj_delete(overlay);
        return std::unexpected("Failed to create Loading contents");
    }
    // Compact Circular Shell geometry; colors stay with the registered product theme.
    lv_obj_set_size(overlay, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
    lv_obj_set_style_bg_color(overlay, lv_color_hex(theme_color("surface.raised")), 0);
    lv_obj_set_style_bg_opa(overlay, LV_OPA_COVER, 0);
    lv_obj_set_style_border_color(overlay, lv_color_hex(theme_color("border.default")), 0);
    lv_obj_set_style_border_width(overlay, 1, 0);
    lv_obj_set_style_radius(overlay, LV_RADIUS_CIRCLE, 0);
    lv_obj_set_style_pad_all(overlay, 12, 0);
    lv_obj_set_style_pad_column(overlay, 10, 0);
    lv_obj_set_flex_flow(overlay, LV_FLEX_FLOW_ROW);
    lv_obj_set_flex_align(overlay, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
    lv_obj_set_size(spinner, 24, 24);
    lv_spinner_set_anim_params(spinner, 1200, 90);
    lv_obj_set_style_arc_width(spinner, 3, LV_PART_MAIN);
    lv_obj_set_style_arc_width(spinner, 3, LV_PART_INDICATOR);
    lv_obj_set_style_arc_color(spinner, lv_color_hex(theme_color("surface.muted")), LV_PART_MAIN);
    lv_obj_set_style_arc_color(spinner, lv_color_hex(theme_color("primary.fill")), LV_PART_INDICATOR);
    lv_label_set_text(label, "Loading");
    lv_obj_set_style_text_font(label, &lv_font_montserrat_18, 0);
    lv_obj_set_style_text_color(label, lv_color_hex(theme_color("text.default")), 0);
    // Keep the whole pill inside the circular edge, scaled to the active display.
    lv_obj_align(overlay, LV_ALIGN_BOTTOM_MID, 0, -lv_obj_get_height(lv_layer_top()) / 10);
    lv_obj_remove_flag(overlay, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_remove_flag(overlay, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_remove_flag(spinner, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_remove_flag(label, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_move_to_index(overlay, 0); // Feedback never takes input or obscures Keyboard/Dialog.
    (startup ? loading_state_->startup : loading_state_->app_wait) = true;
    loading_state_->app_id = app_id;
    loading_state_->overlay = overlay;
    loading_state_->invalidated = false;
    return {};
}

} // namespace espocket
