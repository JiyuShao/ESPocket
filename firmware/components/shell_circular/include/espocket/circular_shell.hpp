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
#include "brookesia/service_helper/media/display.hpp"
#include "brookesia/service_manager/event/registry.hpp"
#include "brookesia/service_manager/service/manager.hpp"
#include "brookesia/system_core.hpp"

namespace espocket {

enum class ShellSurface : uint8_t {
    WatchFace,
    BatteryCard,
    BrightnessCard,
    QuickSettings,
    Launcher,
};

class CircularShell final : public esp_brookesia::system::core::IApp {
public:
    using PowerPressCountProvider = std::function<uint32_t()>;
    using DisplayOnProvider = std::function<bool()>;
    using AppVisibleProvider = std::function<bool()>;
    using SystemHandler = std::function<void()>;
    using AppLaunchHandler = std::function<std::expected<void, std::string>(
                                 std::string_view,
                                 ShellSurface
                             )>;
    using KeyboardResultHandler = std::function<void(
                                      esp_brookesia::system::core::AppId,
                                      esp_brookesia::system::core::KeyboardRequestId,
                                      bool,
                                      std::string
                                  )>;

    explicit CircularShell(
        PowerPressCountProvider power_press_count_provider = {},
        DisplayOnProvider display_on_provider = {},
        AppVisibleProvider app_visible_provider = {},
        SystemHandler power_handler = {},
        SystemHandler screen_timeout_handler = {},
        AppLaunchHandler app_launch_handler = {},
        SystemHandler back_handler = {},
        KeyboardResultHandler keyboard_result_handler = {}
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

    struct HomeGestureState {
        std::atomic_bool consumed = false;
        std::atomic<ShellSurface> surface = ShellSurface::WatchFace;
        std::atomic<uint8_t> pending_gesture = 0;
        std::atomic<uint32_t> activity_generation = 0;
    };

    struct KeyboardState;

    std::expected<void, std::string> configure_home_gesture();
    std::expected<void, std::string> open_app(
        std::string_view manifest_id,
        std::string_view display_name
    );

    void start_status();
    void stop_status();
    void refresh_status();
    void refresh_clock();
    void refresh_wifi();
    void refresh_battery();
    void refresh_brightness();
    std::expected<void, std::string> step_brightness();
    std::expected<void, std::string> toggle_wifi();
    void set_status_text(std::string_view path, std::string text);

    PowerPressCountProvider power_press_count_provider_;
    DisplayOnProvider display_on_provider_;
    AppVisibleProvider app_visible_provider_;
    SystemHandler power_handler_;
    SystemHandler screen_timeout_handler_;
    AppLaunchHandler app_launch_handler_;
    SystemHandler back_handler_;
    KeyboardResultHandler keyboard_result_handler_;
    std::shared_ptr<HomeGestureState> home_gesture_state_;
    std::shared_ptr<KeyboardState> keyboard_state_;
    std::shared_ptr<CallbackState> callback_state_;
    esp_brookesia::system::core::AppContext *context_ = nullptr;
    esp_brookesia::system::core::TimerId home_intent_timer_id_ =
        esp_brookesia::system::core::INVALID_TIMER_ID;
    esp_brookesia::system::core::TimerId status_timer_id_ =
        esp_brookesia::system::core::INVALID_TIMER_ID;
    uint32_t last_power_press_count_ = 0;
    uint32_t last_activity_generation_ = 0;
    int64_t last_activity_us_ = 0;
    bool screen_timeout_latched_ = false;

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
