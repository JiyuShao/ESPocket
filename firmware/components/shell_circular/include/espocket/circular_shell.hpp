#pragma once

#include <atomic>
#include <cstdint>
#include <expected>
#include <functional>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <string_view>

#include "brookesia/lib_utils/signal.hpp"
#include "brookesia/service_manager/event/registry.hpp"
#include "brookesia/service_manager/service/manager.hpp"
#include "brookesia/system_core.hpp"
#include "espocket/shell_gesture.hpp"
#include "espocket/launcher_projection.hpp"

namespace espocket {

struct ShellBackUiState {
    bool default_visible = false;
    bool edge_enabled = false;
    bool edge_reserved = false;
};

struct ShellDeveloperModeControl {
    std::function<bool()> enabled;
    std::function<std::expected<void, std::string>(bool)> set_enabled;
};

struct ShellHost {
    // Immutable product theme resource already registered with GUI Runtime.
    std::function<std::expected<std::string_view, std::string>(std::string_view)> theme_resource;
    std::function<bool()> display_on;
    std::function<bool()> app_visible;
    std::function<void()> screen_timeout;
    std::function<std::expected<void, std::string>(std::string_view, ShellSurface)> launch_app;
    std::function<void()> back;
    std::function<void(esp_brookesia::system::core::AppId,
                       esp_brookesia::system::core::KeyboardRequestId, bool, std::string)> keyboard_result;
    std::function<void(esp_brookesia::system::core::AppId,
                       esp_brookesia::system::core::MessageDialogRequestId, int32_t,
                       esp_brookesia::system::core::MessageDialogCloseReason)> message_dialog_result;
    std::function<ShellBackUiState()> back_ui;
    std::function<void()> expire_back;
    ShellDeveloperModeControl developer_mode;
    std::function<void()> tick;
    // Left=true denotes the left sequence. inward=true advances toward Home.
    std::function<std::expected<void, std::string>(bool left, bool inward)> card_step;
    std::function<void(ShellSurface)> surface_changed;
    std::function<std::expected<double, std::string>()> brightness_read;
    std::function<std::expected<double, std::string>(double)> brightness_set;
    std::function<std::expected<std::vector<LauncherApp>, std::string>(std::string_view)> launcher_apps;
    std::function<uint64_t()> launcher_generation;
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

    std::expected<void, std::string> show_message_dialog(
        esp_brookesia::system::core::AppId app_id,
        esp_brookesia::system::core::MessageDialogRequestId request_id,
        const esp_brookesia::system::core::MessageDialogOptions &options);
    std::expected<void, std::string> update_message_dialog(
        esp_brookesia::system::core::AppId app_id,
        esp_brookesia::system::core::MessageDialogRequestId request_id,
        const esp_brookesia::system::core::MessageDialogOptions &options);
    void hide_message_dialog(esp_brookesia::system::core::AppId app_id,
                             esp_brookesia::system::core::MessageDialogRequestId request_id);

private:
    std::expected<void, std::string> load_theme_colors();
    uint32_t theme_color(std::string_view token) const;
    std::map<std::string, uint32_t, std::less<>> theme_colors_;
    struct CallbackState {
        std::mutex mutex;
        CircularShell *owner = nullptr;
    };

    using HomeGestureState = ShellGestureState;

    struct KeyboardState;
    struct MessageDialogState;
    struct BackOverlayState;

    std::expected<void, std::string> configure_home_gesture();
    std::expected<void, std::string> open_app(
        std::string_view manifest_id,
        std::string_view display_name
    );
    std::expected<void, std::string> render_message_dialog(
        const esp_brookesia::system::core::MessageDialogOptions &options);
    void poll_message_dialog();
    void sync_default_back(bool visible);
    void sync_card_hint(bool visible);
    void refresh_launcher();
    void dispatch_launcher();
    void stop_launcher();

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
    std::shared_ptr<MessageDialogState> message_dialog_state_;
    std::shared_ptr<BackOverlayState> back_overlay_state_;
    std::shared_ptr<CallbackState> callback_state_;
    esp_brookesia::system::core::AppContext *context_ = nullptr;
    bool status_refresh_deferred_ = false;
    esp_brookesia::system::core::TimerId home_intent_timer_id_ =
        esp_brookesia::system::core::INVALID_TIMER_ID;
    esp_brookesia::system::core::TimerId status_timer_id_ =
        esp_brookesia::system::core::INVALID_TIMER_ID;
    uint32_t last_activity_generation_ = 0;
    int64_t last_activity_us_ = 0;
    bool screen_timeout_latched_ = false;
    uint8_t launcher_pull_visual_ = 0;
    int32_t launcher_pull_height_ = 28;
    std::vector<LauncherEntry> launcher_entries_;
    std::string launcher_region_;
    std::vector<std::string> launcher_images_;
    std::mutex launcher_intent_mutex_;
    std::string launcher_intent_;
    esp_brookesia::gui::ScopedConnection launcher_connection_;
    uint64_t launcher_generation_ = UINT64_MAX;
    uint64_t launcher_view_generation_ = 0;
    int64_t launcher_refresh_at_us_ = 0;
    bool launcher_developer_enabled_ = false;
    std::string launcher_language_;

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
