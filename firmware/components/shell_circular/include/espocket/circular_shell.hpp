#pragma once

#include <expected>
#include <string>
#include <string_view>

#include "brookesia/lib_utils/signal.hpp"
#include "brookesia/service_helper/media/display.hpp"
#include "brookesia/service_manager/event/registry.hpp"
#include "brookesia/service_manager/service/manager.hpp"
#include "brookesia/system_core.hpp"

namespace espocket {

class CircularShell final : public esp_brookesia::system::core::IApp {
public:
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

private:
    std::expected<void, std::string> configure_home_gesture();
    std::expected<void, std::string> open_preview();
    std::expected<void, std::string> open_launcher();
    void handle_home_gesture(const esp_brookesia::service::helper::Display::TouchGestureInfo &info);

    void start_status();
    void stop_status();
    void refresh_status();
    void refresh_clock();
    void refresh_wifi();
    void refresh_battery();
    void set_status_text(std::string_view path, std::string text);

    esp_brookesia::system::core::AppContext *context_ = nullptr;
    esp_brookesia::system::core::TimerId status_timer_id_ =
        esp_brookesia::system::core::INVALID_TIMER_ID;
    bool preview_open_ = false;
    int32_t gesture_exit_distance_px_ = 0;

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
