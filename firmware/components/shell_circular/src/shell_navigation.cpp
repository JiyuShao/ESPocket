#include "shell_internal.hpp"

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
    auto output = std::find_if(outputs.begin(), outputs.end(), [](const auto &candidate) {
        return candidate.width > 0 && candidate.height > 0 && candidate.touch.has_value();
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

    gesture_connection_ = display.connect_touch_gesture(
                              output->name,
    [exit_distance_px,
     state = home_gesture_state_,
     display_on_provider = host_.display_on,
     app_visible_provider = host_.app_visible,
     back_ui_provider = host_.back_ui](
        const std::string &, const DisplayService::TouchGestureInfo &info
    ) {
        if (info.event_type == DisplayHelper::TouchGestureEventType::Press) {
            state->consumed.store(false, std::memory_order_release);
            state->launcher_pull_distance.store(0, std::memory_order_release);
            state->launcher_press_started_at_top.store(
                state->surface.load(std::memory_order_acquire) == ShellSurface::Launcher &&
                    state->launcher_scroll_top.load(std::memory_order_acquire) <= 1,
                std::memory_order_release
            );
            if (display_on_provider && !display_on_provider()) {
                return;
            }
            state->activity_generation.fetch_add(1, std::memory_order_acq_rel);
            return;
        }
        if (info.event_type == DisplayHelper::TouchGestureEventType::Release) {
            if ((!app_visible_provider || !app_visible_provider()) &&
                    state->surface.load(std::memory_order_acquire) == ShellSurface::Launcher &&
                    state->launcher_press_started_at_top.load(std::memory_order_acquire) &&
                    state->launcher_pull_distance.load(std::memory_order_acquire) >= exit_distance_px) {
                state->pending_gesture.store(
                    static_cast<uint8_t>(GestureIntent::WatchFace), std::memory_order_release
                );
            } else {
                state->launcher_pull_distance.store(0, std::memory_order_release);
            }
            return;
        }
        if (info.event_type != DisplayHelper::TouchGestureEventType::Pressing ||
                (display_on_provider && !display_on_provider())) {
            return;
        }

        const bool app_visible = app_visible_provider && app_visible_provider();
        const auto surface = state->surface.load(std::memory_order_acquire);
        if (!app_visible && surface == ShellSurface::Launcher &&
                state->launcher_press_started_at_top.load(std::memory_order_acquire) &&
                info.direction == DisplayHelper::TouchGestureDirection::Down) {
            state->launcher_pull_distance.store(
                std::max(0, info.stop_y - info.start_y), std::memory_order_release
            );
            return; // Launcher commits Home on release only.
        }
        if (info.distance_px < exit_distance_px) {
            return;
        }

        GestureIntent intent = GestureIntent::None;
        const bool edge_back =
            (has_gesture_area(info.start_area, DisplayHelper::TouchGestureArea::LeftEdge) &&
             info.direction == DisplayHelper::TouchGestureDirection::Right) ||
            (has_gesture_area(info.start_area, DisplayHelper::TouchGestureArea::RightEdge) &&
             info.direction == DisplayHelper::TouchGestureDirection::Left);
        if (app_visible && edge_back && back_ui_provider && back_ui_provider().edge_enabled) {
            intent = GestureIntent::Back;
        } else if (!app_visible) {
            switch (surface) {
            case ShellSurface::WatchFace:
                if (info.direction == DisplayHelper::TouchGestureDirection::Up) {
                    intent = GestureIntent::Launcher;
                } else if (info.direction == DisplayHelper::TouchGestureDirection::Down) {
                    intent = GestureIntent::QuickSettings;
                } else if (info.direction == DisplayHelper::TouchGestureDirection::Right) {
                    intent = GestureIntent::BatteryCard;
                } else if (info.direction == DisplayHelper::TouchGestureDirection::Left) {
                    intent = GestureIntent::BrightnessCard;
                }
                break;
            case ShellSurface::BatteryCard:
                if (info.direction == DisplayHelper::TouchGestureDirection::Left) {
                    intent = GestureIntent::WatchFace;
                }
                break;
            case ShellSurface::BrightnessCard:
                if (info.direction == DisplayHelper::TouchGestureDirection::Right) {
                    intent = GestureIntent::WatchFace;
                }
                break;
            case ShellSurface::QuickSettings:
                if (info.direction == DisplayHelper::TouchGestureDirection::Up) {
                    intent = GestureIntent::WatchFace;
                }
                break;
            case ShellSurface::Launcher:
                break;
            }
        }
        if (intent == GestureIntent::None) {
            return;
        }

        bool expected = false;
        if (!state->consumed.compare_exchange_strong(
                    expected,
                    true,
                    std::memory_order_acq_rel
                )) {
            return;
        }
        state->pending_gesture.store(static_cast<uint8_t>(intent), std::memory_order_release);
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
