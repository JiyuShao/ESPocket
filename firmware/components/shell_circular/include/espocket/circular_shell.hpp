#pragma once

#include <atomic>
#include <cstdint>
#include <expected>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <string_view>

#include "brookesia/lib_utils/signal.hpp"
#include "brookesia/service_manager/event/registry.hpp"
#include "brookesia/service_manager/service/manager.hpp"
#include "brookesia/system_core.hpp"
#include "espocket/shell_gesture.hpp"

namespace espocket {

struct ShellBackUiState {
    bool default_visible = false;
    bool edge_enabled = false;
};

struct ShellDeveloperModeControl {
    std::function<bool()> enabled;
    std::function<std::expected<void, std::string>(bool)> set_enabled;
};

struct ShellHost {
    std::function<bool()> display_on;
    std::function<bool()> app_visible;
    std::function<void()> screen_timeout;
    std::function<std::expected<void, std::string>(std::string_view, ShellSurface)> launch_app;
    std::function<void()> back;
    std::function<void(esp_brookesia::system::core::AppId,
                       esp_brookesia::system::core::KeyboardRequestId, bool, std::string)> keyboard_result;
    std::function<ShellBackUiState()> back_ui;
    std::function<void()> expire_back;
    ShellDeveloperModeControl developer_mode;
    std::function<void()> tick;
};

class CircularShell final : public esp_brookesia::system::core::IApp {
public:
    using BackUiState = ShellBackUiState;
    using DeveloperModeControl = ShellDeveloperModeControl;

    explicit CircularShell(
        uint32_t display_output_id,
        ShellHost host = {}
    );

    esp_brookesia::system::core::AppManifest get_manifest() const override;
    esp_brookesia::system::core::AppGuiDescriptor get_gui_descriptor() const override;

    std::expected<void, std::string> on_start(
        esp_brookesia::system::core::AppContext &context
    ) override;
    std::expected<void, std::string> on_stop(
        esp_brookesia::system::core::AppContext &context
    ) override;
    std::expected<void, std::string> on_action(
        esp_brookesia::system::core::AppContext &context,
        std::string_view action
    ) override;
    std::expected<void, std::string> on_timer(
        esp_brookesia::system::core::AppContext &context,
        esp_brookesia::system::core::TimerId timer_id,
        std::string_view name
    ) override;

    std::expected<void, std::string> show_watch_face();
    std::expected<void, std::string> show_launcher();
    std::expected<void, std::string> show_surface(ShellSurface surface);
    ShellSurface current_surface() const;
    std::expected<void, std::string> handle_gesture(const ShellGestureEvent &event);
    std::expected<void, std::string> inject_synthetic_touch(int32_t x, int32_t y, bool pressed, bool first);
    std::expected<void, std::string> finish_synthetic_touch(bool cancelled);
    void cancel_gesture_input();
    bool is_watch_face() const;
    std::expected<void, std::string> set_display_on(bool on);
    std::expected<void, std::string> show_keyboard(
        esp_brookesia::system::core::AppId app_id,
        esp_brookesia::system::core::KeyboardRequestId request_id,
        const esp_brookesia::system::core::KeyboardRequestOptions &options
    );
    void hide_keyboard(
        esp_brookesia::system::core::AppId app_id,
        esp_brookesia::system::core::KeyboardRequestId request_id
    );

private:
    struct CallbackState {
        std::mutex mutex;
        CircularShell *owner = nullptr;
    };

    using HomeGestureState = ShellGestureState;

    struct KeyboardState;
    struct BackOverlayState;

    std::expected<void, std::string> configure_home_gesture();
    std::expected<void, std::string> open_app(
        std::string_view manifest_id,
        std::string_view display_name
    );
    void sync_default_back(bool visible);

    void start_status();
    void stop_status();
    void refresh_status();
    void refresh_clock();
    void refresh_wifi();
    void refresh_battery();
    void refresh_brightness();
    void refresh_developer_mode();
    std::expected<void, std::string> step_brightness();
    std::expected<void, std::string> toggle_wifi();
    void set_status_text(std::string_view path, std::string text);

    uint32_t display_output_id_;
    ShellHost host_;
    std::shared_ptr<HomeGestureState> home_gesture_state_;
    std::string touch_output_name_;
    ShellTouchTracker synthetic_touch_tracker_;
    std::shared_ptr<KeyboardState> keyboard_state_;
    std::shared_ptr<BackOverlayState> back_overlay_state_;
    std::shared_ptr<CallbackState> callback_state_;
    esp_brookesia::system::core::AppContext *context_ = nullptr;
    esp_brookesia::system::core::TimerId home_intent_timer_id_ =
        esp_brookesia::system::core::INVALID_TIMER_ID;
    esp_brookesia::system::core::TimerId status_timer_id_ =
        esp_brookesia::system::core::INVALID_TIMER_ID;
    uint32_t last_activity_generation_ = 0;
    int64_t last_activity_us_ = 0;
    bool screen_timeout_latched_ = false;
    uint8_t launcher_pull_visual_ = 0;
    int32_t launcher_pull_height_ = 28;

    esp_brookesia::service::ServiceBinding display_binding_;
    esp_brookesia::service::ServiceBinding wifi_binding_;
    esp_brookesia::service::ServiceBinding device_binding_;
    esp_brookesia::service::ServiceBinding sntp_binding_;
    esp_brookesia::lib_utils::connection gesture_connection_;
    esp_brookesia::service::EventRegistry::SignalConnection wifi_connection_;
    esp_brookesia::service::EventRegistry::SignalConnection battery_connection_;
    esp_brookesia::service::EventRegistry::SignalConnection sntp_state_connection_;
    esp_brookesia::service::EventRegistry::SignalConnection sntp_timezone_connection_;
};

} // namespace espocket
