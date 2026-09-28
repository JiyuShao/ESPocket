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

class CircularShell final : public esp_brookesia::system::core::IApp {
public:
    using ForegroundToken = uint64_t;
    using ForegroundTokenProvider = std::function<ForegroundToken()>;
    using HomeHandler = std::function<void(ForegroundToken)>;
    using KeyboardResultHandler = std::function<void(
                                      esp_brookesia::system::core::AppId,
                                      esp_brookesia::system::core::KeyboardRequestId,
                                      bool,
                                      std::string
                                  )>;

    explicit CircularShell(
        ForegroundTokenProvider foreground_token_provider = {},
        HomeHandler home_handler = {},
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

    std::expected<void, std::string> restore_launcher();
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
        std::atomic<ForegroundToken> gesture_token = 0;
        std::atomic<ForegroundToken> pending_token = 0;
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
    void set_status_text(std::string_view path, std::string text);

    ForegroundTokenProvider foreground_token_provider_;
    HomeHandler home_handler_;
    KeyboardResultHandler keyboard_result_handler_;
    std::shared_ptr<HomeGestureState> home_gesture_state_;
    std::shared_ptr<KeyboardState> keyboard_state_;
    std::shared_ptr<CallbackState> callback_state_;
    esp_brookesia::system::core::AppContext *context_ = nullptr;
    esp_brookesia::system::core::TimerId home_intent_timer_id_ =
        esp_brookesia::system::core::INVALID_TIMER_ID;
    esp_brookesia::system::core::TimerId status_timer_id_ =
        esp_brookesia::system::core::INVALID_TIMER_ID;

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
