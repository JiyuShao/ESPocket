#include "shell_internal.hpp"

namespace espocket {

// Called with the LVGL lock and presentation-state mutex held.
std::expected<void, std::string> CircularShell::render_message_dialog(
    const esp_brookesia::system::core::MessageDialogOptions &options)
{
    if (options.buttons.size() > 3 || options.auto_close_ms < 0) {
        return std::unexpected("Unsupported message dialog options");
    }
    auto *overlay = lv_obj_create(lv_layer_top());
    if (!overlay) return std::unexpected("Failed to create message dialog overlay");
    lv_obj_remove_flag(overlay, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_size(overlay, lv_pct(100), lv_pct(100));
    lv_obj_center(overlay);
    lv_obj_set_style_bg_color(overlay, lv_color_hex(0x07090d), 0);
    lv_obj_set_style_bg_opa(overlay, LV_OPA_80, 0);
    lv_obj_set_style_border_width(overlay, 0, 0);
    lv_obj_set_style_radius(overlay, 0, 0);
    auto *panel = lv_obj_create(overlay);
    if (!panel) { lv_obj_delete(overlay); return std::unexpected("Failed to create dialog panel"); }
    const bool light = context_->gui().get_theme() == "light";
    lv_obj_remove_flag(panel, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_size(panel, 316, LV_SIZE_CONTENT);
    lv_obj_center(panel);
    lv_obj_set_style_bg_color(panel, lv_color_hex(light ? 0xf2f5f8 : 0x202934), 0);
    lv_obj_set_style_bg_opa(panel, LV_OPA_COVER, 0);
    lv_obj_set_style_border_width(panel, 0, 0);
    lv_obj_set_style_radius(panel, 20, 0);
    lv_obj_set_style_pad_all(panel, 16, 0);
    lv_obj_set_style_pad_row(panel, 8, 0);
    lv_obj_set_flex_flow(panel, LV_FLEX_FLOW_COLUMN);
    auto *body = lv_obj_create(panel);
    auto *text = body ? lv_label_create(body) : nullptr;
    if (!body || !text) { lv_obj_delete(overlay); return std::unexpected("Failed to create dialog text"); }
    lv_obj_set_width(body, lv_pct(100));
    lv_obj_set_height(body, LV_SIZE_CONTENT);
    lv_obj_set_style_max_height(body, 112, 0);
    lv_obj_set_style_bg_opa(body, LV_OPA_TRANSP, 0);
    lv_obj_set_style_border_width(body, 0, 0);
    lv_obj_set_style_pad_all(body, 0, 0);
    std::string content;
    using Icon = esp_brookesia::system::core::MessageDialogIcon;
    if (options.icon == Icon::Question) content = "?  ";
    else if (options.icon == Icon::Warning || options.icon == Icon::Critical) content = "!  ";
    else if (options.icon == Icon::Information) content = "i  ";
    content += options.text;
    if (!options.informative_text.empty()) content += "\n\n" + options.informative_text;
    lv_label_set_text(text, content.c_str());
    lv_label_set_long_mode(text, LV_LABEL_LONG_MODE_WRAP);
    lv_obj_set_width(text, lv_pct(100));
    lv_obj_set_style_text_color(text, lv_color_hex(light ? 0x152233 : 0xf1f5f9), 0);
    lv_obj_set_style_text_font(text, &lv_font_montserrat_18, 0);
    for (size_t i = 0; i < options.buttons.size(); ++i) {
        auto *button = lv_button_create(panel);
        auto *label = button ? lv_label_create(button) : nullptr;
        if (!button || !label) { lv_obj_delete(overlay); return std::unexpected("Failed to create dialog button"); }
        lv_obj_set_size(button, lv_pct(100), 46);
        lv_obj_set_style_radius(button, 16, 0);
        const bool destructive = options.buttons[i].role ==
                                 esp_brookesia::system::core::MessageDialogButtonRole::Destructive;
        lv_obj_set_style_bg_color(button, lv_color_hex(destructive ? 0xa52832 : 0x2157d5), 0);
        lv_obj_set_style_bg_opa(button, LV_OPA_COVER, 0);
        lv_obj_set_style_border_width(button, 0, 0);
        lv_label_set_text(label, options.buttons[i].text.c_str());
        lv_obj_set_style_text_color(label, lv_color_hex(0xffffff), 0);
        lv_obj_set_style_text_font(label, &lv_font_montserrat_18, 0);
        lv_obj_set_width(label, lv_pct(100));
        lv_label_set_long_mode(label, LV_LABEL_LONG_MODE_DOTS);
        lv_obj_set_style_text_align(label, LV_TEXT_ALIGN_CENTER, 0);
        lv_obj_center(label);
        lv_obj_add_event_cb(button, [](lv_event_t *event) {
            auto *binding = static_cast<MessageDialogState::Button *>(lv_event_get_user_data(event));
            std::lock_guard lock(binding->state->mutex);
            if (binding->state->request_id == esp_brookesia::system::core::INVALID_MESSAGE_DIALOG_REQUEST_ID ||
                    binding->state->result_pending) return;
            binding->state->button_index = binding->index;
            binding->state->result_pending = true;
        }, LV_EVENT_CLICKED, &message_dialog_state_->buttons[i]);
    }
    if (message_dialog_state_->overlay) lv_obj_delete(message_dialog_state_->overlay);
    message_dialog_state_->overlay = overlay;
    message_dialog_state_->result_pending = false;
    message_dialog_state_->button_index = -1;
    message_dialog_state_->deadline_us = options.auto_close_ms > 0 ?
        esp_timer_get_time() + static_cast<int64_t>(options.auto_close_ms) * 1000 : 0;
    return {};
}

std::expected<void, std::string> CircularShell::show_message_dialog(
    esp_brookesia::system::core::AppId app_id,
    esp_brookesia::system::core::MessageDialogRequestId request_id,
    const esp_brookesia::system::core::MessageDialogOptions &options)
{
    if (!context_ || !message_dialog_state_ ||
            request_id == esp_brookesia::system::core::INVALID_MESSAGE_DIALOG_REQUEST_ID) {
        return std::unexpected("Circular Shell is unavailable for message dialog");
    }
    LvglLock lock;
    if (!lock) return std::unexpected("Failed to lock LVGL for message dialog");
    std::lock_guard state_lock(message_dialog_state_->mutex);
    if (message_dialog_state_->overlay) return std::unexpected("Another message dialog is active");
    auto result = render_message_dialog(options);
    if (!result) return result;
    message_dialog_state_->app_id = app_id;
    message_dialog_state_->request_id = request_id;
    if (home_gesture_state_) home_gesture_state_->modal_active.store(true, std::memory_order_release);
    ESP_LOGI(SHELL_TAG, "System message dialog opened: request=%" PRIu64, request_id);
    return {};
}

std::expected<void, std::string> CircularShell::update_message_dialog(
    esp_brookesia::system::core::AppId app_id,
    esp_brookesia::system::core::MessageDialogRequestId request_id,
    const esp_brookesia::system::core::MessageDialogOptions &options)
{
    if (!context_ || !message_dialog_state_) return std::unexpected("Circular Shell is unavailable");
    LvglLock lock;
    if (!lock) return std::unexpected("Failed to lock LVGL for message dialog update");
    std::lock_guard state_lock(message_dialog_state_->mutex);
    if (!message_dialog_state_->overlay || message_dialog_state_->app_id != app_id ||
            message_dialog_state_->request_id != request_id) return std::unexpected("Message dialog owner mismatch");
    return render_message_dialog(options);
}

void CircularShell::hide_message_dialog(esp_brookesia::system::core::AppId app_id,
    esp_brookesia::system::core::MessageDialogRequestId request_id)
{
    if (!message_dialog_state_) return;
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
    if (home_gesture_state_) home_gesture_state_->modal_active.store(false, std::memory_order_release);
    ESP_LOGI(SHELL_TAG, "System message dialog closed: request=%" PRIu64, request_id);
}

void CircularShell::poll_message_dialog()
{
    if (!message_dialog_state_ || !host_.message_dialog_result) return;
    esp_brookesia::system::core::AppId app_id;
    esp_brookesia::system::core::MessageDialogRequestId request_id;
    int32_t index;
    auto reason = esp_brookesia::system::core::MessageDialogCloseReason::Button;
    {
        std::lock_guard lock(message_dialog_state_->mutex);
        if (message_dialog_state_->request_id == esp_brookesia::system::core::INVALID_MESSAGE_DIALOG_REQUEST_ID) return;
        if (!message_dialog_state_->result_pending) {
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
        if (message_dialog_state_->request_id == request_id) return; // Retry failed UI cleanup.
    }
    host_.message_dialog_result(app_id, request_id, index, reason);
}

} // namespace espocket
