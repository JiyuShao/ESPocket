#include "shell_internal.hpp"

namespace espocket {

void CircularShell::start_status()
{
    set_status_text(WATCH_FACE_TIME_PATH, "--:--");
    set_status_text(WATCH_FACE_DATE_PATH, "Waiting for sync");

    auto &manager = esp_brookesia::service::ServiceManager::get_instance();

    if (WifiHelper::is_available()) {
        wifi_binding_ = manager.bind(WifiHelper::get_name().data());
        if (wifi_binding_.is_valid()) {
            wifi_connection_ = WifiHelper::subscribe_event(
                                   WifiHelper::EventId::GeneralEventHappened,
            [state = callback_state_](const std::string &, const std::string & event, bool unexpected) {
                std::lock_guard lock(state->mutex);
                if (state->owner == nullptr) {
                    return;
                }
                if (unexpected) {
                    ESP_LOGW(SHELL_TAG, "Wi-Fi reported unexpected event: %s", event.c_str());
                }
                if (event == "Connected") {
                    state->owner->set_status_text(QUICK_WIFI_PATH, "Wi-Fi: linked (tap to stop)");
                } else if (event == "Deinited" || event == "Inited" || event == "Stopped" ||
                           event == "Started" || event == "Disconnected") {
                    state->owner->set_status_text(QUICK_WIFI_PATH, "Wi-Fi: off/unlinked (tap)");
                } else {
                    state->owner->set_status_text(QUICK_WIFI_PATH, "Wi-Fi: ?");
                }
            }
                               );
        }
    }

    if (DeviceHelper::is_available()) {
        device_binding_ = manager.bind(DeviceHelper::get_name().data());
        if (device_binding_.is_valid()) {
            battery_connection_ = DeviceHelper::subscribe_event(
                                      DeviceHelper::EventId::PowerBatteryStateChanged,
            [callback_state = callback_state_](
                const std::string &, const esp_brookesia::service::EventItemMap &items
            ) {
                std::lock_guard lock(callback_state->mutex);
                if (callback_state->owner == nullptr) {
                    return;
                }
                auto item = items.find("State");
                if (item == items.end() || !std::holds_alternative<boost::json::object>(item->second)) {
                    callback_state->owner->set_status_text(BATTERY_CARD_PATH, "Battery: ?");
                    callback_state->owner->set_status_text(QUICK_BATTERY_PATH, "Battery: ?");
                    return;
                }
                DeviceHelper::PowerBatteryState state;
                if (!BROOKESIA_DESCRIBE_FROM_JSON(std::get<boost::json::object>(item->second), state) ||
                        !state.is_present || !state.percentage.has_value()) {
                    callback_state->owner->set_status_text(BATTERY_CARD_PATH, "Battery: ?");
                    callback_state->owner->set_status_text(QUICK_BATTERY_PATH, "Battery: ?");
                    return;
                }
                const auto text = "Battery: " + std::to_string(*state.percentage) + "%";
                callback_state->owner->set_status_text(BATTERY_CARD_PATH, text);
                callback_state->owner->set_status_text(QUICK_BATTERY_PATH, text);
            }
                                  );
        }
    }

    if (SNTPHelper::is_available()) {
        sntp_binding_ = manager.bind(SNTPHelper::get_name().data());
        if (sntp_binding_.is_valid()) {
            sntp_state_connection_ = SNTPHelper::subscribe_event(
                                         SNTPHelper::EventId::StateChanged,
            [state = callback_state_](const std::string &, const std::string &) {
                std::lock_guard lock(state->mutex);
                if (state->owner != nullptr) {
                    state->owner->refresh_clock();
                }
            }
                                     );
            sntp_timezone_connection_ = SNTPHelper::subscribe_event(
                                            SNTPHelper::EventId::TimezoneChanged,
            [state = callback_state_](const std::string &, const std::string &) {
                std::lock_guard lock(state->mutex);
                if (state->owner != nullptr) {
                    state->owner->refresh_clock();
                }
            }
                                        );

            auto state = SNTPHelper::call_function_sync<std::string>(SNTPHelper::FunctionId::GetState);
            if (state && *state == "Stopped") {
                auto started = SNTPHelper::call_function_sync<void>(SNTPHelper::FunctionId::Start);
                if (!started) {
                    ESP_LOGW(SHELL_TAG, "SNTP start failed: %s", started.error().c_str());
                }
            }
        }
    }

    refresh_status();
    auto timer = context_->timer().start_periodic(STATUS_TIMER, STATUS_INTERVAL_MS);
    if (!timer) {
        ESP_LOGW(SHELL_TAG, "Status fallback timer unavailable: %s", timer.error().c_str());
    } else {
        status_timer_id_ = *timer;
    }
}

void CircularShell::stop_status()
{
    if (context_ != nullptr && status_timer_id_ != esp_brookesia::system::core::INVALID_TIMER_ID) {
        (void)context_->timer().stop(status_timer_id_);
    }
    status_timer_id_ = esp_brookesia::system::core::INVALID_TIMER_ID;
    wifi_connection_.disconnect();
    battery_connection_.disconnect();
    sntp_state_connection_.disconnect();
    sntp_timezone_connection_.disconnect();
    if (callback_state_) {
        std::lock_guard lock(callback_state_->mutex);
        callback_state_->owner = nullptr;
    }
    wifi_binding_.release();
    device_binding_.release();
    sntp_binding_.release();
}

void CircularShell::refresh_status()
{
    refresh_clock();
    refresh_wifi();
    refresh_battery();
    refresh_brightness();
    refresh_developer_mode();
}

void CircularShell::refresh_developer_mode()
{
    set_status_text(
        QUICK_DEVELOPER_MODE_PATH,
        host_.developer_mode.enabled && host_.developer_mode.enabled() ?
            "Developer Mode: On" : "Developer Mode: Off"
    );
}

void CircularShell::refresh_clock()
{
    std::string text = "--:--";
    std::string date = "Waiting for sync";
    if (sntp_binding_.is_valid()) {
        auto synced = SNTPHelper::call_function_sync<bool>(SNTPHelper::FunctionId::IsTimeSynced);
        if (synced && *synced) {
            text = make_clock_text();
            date = make_date_text();
        }
    }
    set_status_text(WATCH_FACE_TIME_PATH, std::move(text));
    set_status_text(WATCH_FACE_DATE_PATH, std::move(date));
}

void CircularShell::refresh_wifi()
{
    if (!wifi_binding_.is_valid()) {
        set_status_text(QUICK_WIFI_PATH, "Wi-Fi: ?");
        return;
    }
    auto state = WifiHelper::call_function_sync<std::string>(WifiHelper::FunctionId::GetGeneralState);
    if (!state) {
        set_status_text(QUICK_WIFI_PATH, "Wi-Fi: ?");
    } else if (*state == "Connected") {
        set_status_text(QUICK_WIFI_PATH, "Wi-Fi: linked (tap to stop)");
    } else if (*state == "Idle" || *state == "Initing" || *state == "Inited" || *state == "Deiniting" ||
               *state == "Starting" || *state == "Started" || *state == "Stopping" ||
               *state == "Connecting" || *state == "Disconnecting") {
        set_status_text(QUICK_WIFI_PATH, "Wi-Fi: off/unlinked (tap)");
    } else {
        set_status_text(QUICK_WIFI_PATH, "Wi-Fi: ?");
    }
}

void CircularShell::refresh_battery()
{
    if (!device_binding_.is_valid()) {
        set_status_text(BATTERY_CARD_PATH, "Battery: ?");
        set_status_text(QUICK_BATTERY_PATH, "Battery: ?");
        return;
    }
    auto value = DeviceHelper::call_function_sync<boost::json::object>(
                     DeviceHelper::FunctionId::GetPowerBatteryState
                 );
    DeviceHelper::PowerBatteryState state;
    if (!value || !BROOKESIA_DESCRIBE_FROM_JSON(*value, state) || !state.is_present ||
            !state.percentage.has_value()) {
        set_status_text(BATTERY_CARD_PATH, "Battery: ?");
        set_status_text(QUICK_BATTERY_PATH, "Battery: ?");
        return;
    }
    const auto text = "Battery: " + std::to_string(*state.percentage) + "%";
    set_status_text(BATTERY_CARD_PATH, text);
    set_status_text(QUICK_BATTERY_PATH, text);
}

void CircularShell::refresh_brightness()
{
    auto value = host_.brightness_read ? host_.brightness_read() :
                 std::expected<double, std::string>(std::unexpected("brightness_unavailable"));
    const auto text = value ? "Brightness: " + std::to_string(static_cast<int>(*value)) + "%" :
                             "Brightness: ?";
    set_status_text(BRIGHTNESS_CARD_PATH, text);
    set_status_text(QUICK_BRIGHTNESS_PATH, text);
}

std::expected<void, std::string> CircularShell::step_brightness()
{
    if (!host_.brightness_read || !host_.brightness_set) return std::unexpected("brightness_unavailable");
    auto current = host_.brightness_read();
    if (!current) return std::unexpected(current.error());
    const double next = *current >= 100.0 ? 20.0 : std::min(100.0, *current + 20.0);
    auto result = host_.brightness_set(next);
    if (!result) return std::unexpected(result.error());
    refresh_brightness();
    return {};
}

std::expected<void, std::string> CircularShell::toggle_wifi()
{
    if (!wifi_binding_.is_valid()) {
        return std::unexpected("Wi-Fi service is unavailable");
    }
    auto state = WifiHelper::call_function_sync<std::string>(WifiHelper::FunctionId::GetGeneralState);
    if (!state) {
        return std::unexpected("Failed to read Wi-Fi state: " + state.error());
    }
    if (*state == "Idle") {
        auto init = WifiHelper::call_function_sync<void>(
                        WifiHelper::FunctionId::TriggerGeneralAction,
                        BROOKESIA_DESCRIBE_TO_STR(WifiHelper::GeneralAction::Init)
                    );
        if (!init) {
            return std::unexpected("Failed to initialize Wi-Fi: " + init.error());
        }
        *state = "Inited";
    }
    const bool enabled = *state == "Started" || *state == "Connecting" ||
                         *state == "Connected" || *state == "Disconnecting";
    const auto action = enabled ? WifiHelper::GeneralAction::Stop : WifiHelper::GeneralAction::Start;
    auto result = WifiHelper::call_function_sync<void>(
                      WifiHelper::FunctionId::TriggerGeneralAction,
                      BROOKESIA_DESCRIBE_TO_STR(action)
                  );
    if (!result) {
        return std::unexpected("Failed to toggle Wi-Fi: " + result.error());
    }
    refresh_wifi();
    return {};
}

void CircularShell::set_status_text(std::string_view path, std::string text)
{
    if (context_ == nullptr) {
        return;
    }
    auto result = context_->gui().set_text(path, text);
    if (!result) {
        ESP_LOGW(SHELL_TAG, "Status update failed at %.*s: %s", static_cast<int>(path.size()), path.data(), result.error().c_str());
    }
}

} // namespace espocket
