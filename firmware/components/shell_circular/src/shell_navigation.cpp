#include "shell_internal.hpp"

#include <cmath>

namespace espocket {

void CircularShell::sync_default_back(bool visible)
{
    if (!back_overlay_state_ || visible == (back_overlay_state_->button != nullptr)) {
        return;
    }
    LvglLock lock;
    if (!lock) {
        ESP_LOGW(SHELL_TAG, "Failed to lock LVGL for default Back");
        return;
    }
    if (!visible) {
        if (lv_obj_is_valid(back_overlay_state_->button)) {
            lv_obj_delete(back_overlay_state_->button);
        }
        back_overlay_state_->button = nullptr;
        back_overlay_state_->clicked.store(false, std::memory_order_release);
        return;
    }
    auto *button = lv_button_create(lv_layer_top());
    if (button == nullptr) {
        ESP_LOGW(SHELL_TAG, "Failed to create default Back button");
        return;
    }
    lv_obj_set_size(button, 98, 52);
    lv_obj_align(button, LV_ALIGN_TOP_MID, -78, 26);
    lv_obj_set_style_bg_color(button, lv_color_hex(0x34465f), 0);
    lv_obj_set_style_radius(button, 24, 0);
    auto *label = lv_label_create(button);
    if (label == nullptr) {
        lv_obj_delete(button);
        return;
    }
    lv_label_set_text(label, "< Back");
    lv_obj_set_style_text_color(label, lv_color_hex(0xffffff), 0);
    lv_obj_set_style_text_font(label, &lv_font_montserrat_18, 0);
    lv_obj_center(label);
    lv_obj_add_event_cb(
        button,
        [](lv_event_t *event) {
            auto *state = static_cast<BackOverlayState *>(lv_event_get_user_data(event));
            state->clicked.store(true, std::memory_order_release);
        },
        LV_EVENT_CLICKED,
        back_overlay_state_.get()
    );
    back_overlay_state_->button = button;
}

std::expected<void, std::string> CircularShell::configure_home_gesture()
{
    if (!DisplayHelper::is_available()) {
        return std::unexpected("Display service is unavailable for Home gesture");
    }

    display_binding_ = esp_brookesia::service::ServiceManager::get_instance().bind(
                           DisplayHelper::get_name().data()
                       );
    if (!display_binding_.is_valid()) {
        return std::unexpected("Failed to bind Display service for Home gesture");
    }

    auto &display = DisplayService::get_instance();
    auto outputs = display.get_outputs();
    auto output = std::find_if(outputs.begin(), outputs.end(), [this](const auto &candidate) {
        return candidate.id == display_output_id_ && candidate.width > 0 && candidate.height > 0 && candidate.touch.has_value();
    });
    if (output == outputs.end()) {
        return std::unexpected("No touch-capable Display output is available for Home gesture");
    }

    DisplayService::TouchGestureConfig config;
    config.enabled = true;
    config.detect_period_ms = 20;
    config.direction_lock_enabled = true;
    config.release_debounce_ms = 40;
    config.threshold.horizontal_edge = gesture_horizontal_edge_px(output->width);
    config.threshold.vertical_edge = gesture_vertical_edge_px(output->height);
    const auto exit_distance_px = gesture_exit_distance_px(static_cast<int32_t>(output->height));
    home_gesture_state_->launcher_return_threshold.store(exit_distance_px, std::memory_order_release);
    auto config_result = display.set_touch_gesture_config(output->id, config);
    if (!config_result) {
        return std::unexpected("Failed to configure Home gesture: " + config_result.error());
    }

    auto resolved = display.get_touch_gesture_config(output->id);
    if (!resolved) { return std::unexpected(resolved.error()); }
    touch_output_name_ = output->name;
    synthetic_touch_tracker_.geometry = {
        .width = static_cast<int32_t>(output->width),
        .horizontal_edge = resolved->threshold.horizontal_edge,
        .vertical_edge = resolved->threshold.vertical_edge,
        .horizontal_threshold = resolved->threshold.direction_horizon,
        .vertical_threshold = resolved->threshold.direction_vertical,
        .direction_tan = std::tan(resolved->threshold.direction_angle * 3.14159265F / 180.0F),
        .direction_lock = resolved->direction_lock_enabled,
    };
    gesture_connection_ = display.connect_touch_gesture(
                              output->name,
    [state = home_gesture_state_,
     display_on_provider = host_.display_on,
     app_visible_provider = host_.app_visible,
     back_ui_provider = host_.back_ui](
        const std::string &, const DisplayService::TouchGestureInfo &info
    ) {
        std::lock_guard input_lock(state->input_mutex);
        if (state->synthetic_input_active.load(std::memory_order_acquire)) { return; }
        ShellGestureEvent event;
        switch (info.event_type) {
        case DisplayHelper::TouchGestureEventType::Press: event.phase = ShellGesturePhase::Press; break;
        case DisplayHelper::TouchGestureEventType::Pressing: event.phase = ShellGesturePhase::Pressing; break;
        case DisplayHelper::TouchGestureEventType::Release: event.phase = ShellGesturePhase::Release; break;
        }
        switch (info.direction) {
        case DisplayHelper::TouchGestureDirection::None: event.direction = ShellGestureDirection::None; break;
        case DisplayHelper::TouchGestureDirection::Up: event.direction = ShellGestureDirection::Up; break;
        case DisplayHelper::TouchGestureDirection::Down: event.direction = ShellGestureDirection::Down; break;
        case DisplayHelper::TouchGestureDirection::Left: event.direction = ShellGestureDirection::Left; break;
        case DisplayHelper::TouchGestureDirection::Right: event.direction = ShellGestureDirection::Right; break;
        }
        event.left_edge = has_gesture_area(info.start_area, DisplayHelper::TouchGestureArea::LeftEdge);
        event.right_edge = has_gesture_area(info.start_area, DisplayHelper::TouchGestureArea::RightEdge);
        event.start_y = info.start_y;
        event.stop_y = info.stop_y;
        event.distance_px = info.distance_px;
        process_shell_gesture(*state, event, {
            .display_on = !display_on_provider || display_on_provider(),
            .app_visible = app_visible_provider && app_visible_provider(),
            .edge_back_enabled = back_ui_provider && back_ui_provider().edge_enabled,
        });
    }
                          );
    if (!gesture_connection_.connected()) {
        return std::unexpected("Failed to subscribe Home gesture events");
    }

    ESP_LOGI(
        SHELL_TAG,
        "Navigation gesture ready: output=%s exit=%" PRId32 "px edge=%" PRIu16 "px",
        output->name.c_str(),
        exit_distance_px,
        config.threshold.vertical_edge
    );
    return {};
}

std::expected<void, std::string> CircularShell::handle_gesture(const ShellGestureEvent &event)
{
    if (!home_gesture_state_) {
        return std::unexpected("Shell gesture input is unavailable");
    }
    std::lock_guard input_lock(home_gesture_state_->input_mutex);
    process_shell_gesture(*home_gesture_state_, event, {
        .display_on = !host_.display_on || host_.display_on(),
        .app_visible = host_.app_visible && host_.app_visible(),
        .edge_back_enabled = host_.back_ui && host_.back_ui().edge_enabled,
    });
    return {};
}

std::expected<void, std::string> CircularShell::open_app(
    std::string_view manifest_id,
    std::string_view display_name
)
{
    if (context_ == nullptr) {
        return std::unexpected("Circular Shell is not running");
    }

    if (!host_.launch_app) {
        return std::unexpected("System app launch handler is unavailable");
    }
    const auto source = current_surface();
    auto result = host_.launch_app(manifest_id, source);
    if (!result) {
        return std::unexpected("Failed to start " + std::string(display_name) + ": " + result.error());
    }

    ESP_LOGI(LAUNCHER_TAG, "Opened %.*s", static_cast<int>(display_name.size()), display_name.data());
    return {};
}

std::expected<void, std::string> CircularShell::show_watch_face()
{
    return show_surface(ShellSurface::WatchFace);
}

std::expected<void, std::string> CircularShell::show_launcher()
{
    return show_surface(ShellSurface::Launcher);
}

std::expected<void, std::string> CircularShell::show_surface(ShellSurface surface)
{
    if (context_ == nullptr) {
        return std::unexpected("Circular Shell is not running");
    }
    std::string_view action;
    switch (surface) {
    case ShellSurface::WatchFace: action = "open_watch_face"; break;
    case ShellSurface::BatteryCard: action = "open_battery_card"; break;
    case ShellSurface::BrightnessCard: action = "open_brightness_card"; break;
    case ShellSurface::QuickSettings: action = "open_quick_settings"; break;
    case ShellSurface::Launcher: action = "open_launcher"; break;
    }
    auto result = context_->gui().trigger_screen_flow(PAGE_FLOW, action);
    if (result && home_gesture_state_) {
        home_gesture_state_->surface.store(surface, std::memory_order_release);
        home_gesture_state_->activity_generation.fetch_add(1, std::memory_order_acq_rel);
        if (surface == ShellSurface::Launcher) {
            home_gesture_state_->launcher_scroll_top.store(100000, std::memory_order_release);
            home_gesture_state_->launcher_pull_distance.store(0, std::memory_order_release);
            (void)context_->gui().scroll_to("/launcher", 0, 0, false);
        } else {
            home_gesture_state_->launcher_pull_distance.store(0, std::memory_order_release);
        }
    }
    return result;
}

ShellSurface CircularShell::current_surface() const
{
    return home_gesture_state_ ?
           home_gesture_state_->surface.load(std::memory_order_acquire) :
           ShellSurface::WatchFace;
}

bool CircularShell::is_watch_face() const
{
    return current_surface() == ShellSurface::WatchFace;
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
    if (on) {
        last_activity_us_ = esp_timer_get_time();
        screen_timeout_latched_ = false;
    }
    return {};
}

} // namespace espocket

namespace espocket {

std::expected<void, std::string> CircularShell::inject_synthetic_touch(
    int32_t x, int32_t y, bool pressed, bool first)
{
    if (!home_gesture_state_ || touch_output_name_.empty()) {
        return std::unexpected("invalid_state");
    }
    if (first) {
        std::lock_guard input_lock(home_gesture_state_->input_mutex);
        reset_shell_gesture(*home_gesture_state_, true);
        home_gesture_state_->synthetic_input_active.store(true, std::memory_order_release);
    }
    auto &display = DisplayService::get_instance();
    auto injected = pressed ? display.inject_touch(touch_output_name_, x, y) :
                    display.inject_touch(touch_output_name_, std::vector<DisplayService::TouchPoint>{});
    if (!injected) { return std::unexpected("internal"); }
    return handle_gesture(synthetic_touch_tracker_.sample(x, y, pressed, first));
}

std::expected<void, std::string> CircularShell::finish_synthetic_touch(bool cancelled)
{
    const bool injected = home_gesture_state_ &&
        home_gesture_state_->synthetic_input_active.load(std::memory_order_acquire);
    if (injected && cancelled) {
        cancel_gesture_input();
        if (esp_lv_adapter_lock(100) != ESP_OK) { return std::unexpected("internal"); }
        // Abort a press without manufacturing a CLICKED event on cleanup.
        lv_indev_reset(nullptr, nullptr);
        esp_lv_adapter_unlock();
    }
    // Display owns the override. Shell may have restarted after a failed cleanup.
    if (touch_output_name_.empty()) { return std::unexpected("invalid_state"); }
    auto cleared = DisplayService::get_instance().clear_injected_touch(touch_output_name_);
    if (!cleared) { return std::unexpected("internal"); }
    if (injected) {
        std::lock_guard input_lock(home_gesture_state_->input_mutex);
        reset_shell_gesture(*home_gesture_state_, cancelled);
        home_gesture_state_->synthetic_input_active.store(false, std::memory_order_release);
    }
    return {};
}

} // namespace espocket

namespace espocket {

void CircularShell::cancel_gesture_input()
{
    if (!home_gesture_state_) { return; }
    std::lock_guard input_lock(home_gesture_state_->input_mutex);
    reset_shell_gesture(*home_gesture_state_, true);
}

} // namespace espocket
