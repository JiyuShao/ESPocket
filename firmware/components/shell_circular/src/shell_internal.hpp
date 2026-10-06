#pragma once

#include "espocket/circular_shell.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cinttypes>
#include <cstdio>
#include <ctime>
#include <mutex>
#include <string>
#include <utility>

#include "boost/json/object.hpp"
#include "brookesia/lib_utils/describe_helpers.hpp"
#include "brookesia/service_display/service_display.hpp"
#include "brookesia/service_helper/media/display.hpp"
#include "brookesia/service_helper/network/sntp.hpp"
#include "brookesia/service_helper/network/wifi.hpp"
#include "brookesia/service_helper/system/device.hpp"
#include "esp_log.h"
#include "esp_lv_adapter.h"
#include "esp_timer.h"
#include "lvgl.h"
#include "sdkconfig.h"

#ifndef CONFIG_ESPOCKET_M6_SCREEN_TIMEOUT_SECONDS
#define CONFIG_ESPOCKET_M6_SCREEN_TIMEOUT_SECONDS 30
#endif

namespace espocket {
namespace {

constexpr char SHELL_TAG[] = "ESPocket.Shell";
constexpr char LAUNCHER_TAG[] = "ESPocket.Launcher";
constexpr std::string_view HELLO_NATIVE_MANIFEST_ID = "espocket.app.hello";
constexpr std::string_view HELLO_RUNTIME_MANIFEST_ID = "espocket.app.hello_runtime";
constexpr std::string_view SETTINGS_MANIFEST_ID = "brookesia.general.settings";
constexpr std::string_view APP_STORE_MANIFEST_ID = "brookesia.general.app_store";
constexpr std::string_view OPEN_HELLO_NATIVE_ACTION = "shell.open_hello_native";
constexpr std::string_view OPEN_HELLO_RUNTIME_ACTION = "shell.open_hello_runtime";
constexpr std::string_view OPEN_SETTINGS_ACTION = "shell.open_settings";
constexpr std::string_view OPEN_SETTINGS_CARD_ACTION = "shell.open_settings_card";
constexpr std::string_view OPEN_SETTINGS_QUICK_ACTION = "shell.open_settings_quick";
constexpr std::string_view OPEN_APP_STORE_ACTION = "shell.open_app_store";
constexpr std::string_view OPEN_DYNAMIC_APP_ACTION = "shell.open_dynamic_app";
constexpr std::string_view STEP_BRIGHTNESS_ACTION = "shell.step_brightness";
constexpr std::string_view STEP_BRIGHTNESS_QUICK_ACTION = "shell.step_brightness_quick";
constexpr std::string_view TOGGLE_WIFI_ACTION = "shell.toggle_wifi";
constexpr std::string_view TOGGLE_DEVELOPER_MODE_ACTION = "shell.toggle_developer_mode";
constexpr std::string_view PAGE_FLOW = "shell_pages";
constexpr std::string_view WATCH_FACE_TIME_PATH = "/watch_face/time";
constexpr std::string_view WATCH_FACE_DATE_PATH = "/watch_face/date";
constexpr std::string_view BATTERY_CARD_PATH = "/battery_card/value";
constexpr std::string_view BRIGHTNESS_CARD_PATH = "/brightness_card/value";
constexpr std::string_view QUICK_BATTERY_PATH = "/quick_settings/battery";
constexpr std::string_view QUICK_BRIGHTNESS_PATH = "/quick_settings/brightness_action/brightness";
constexpr std::string_view QUICK_WIFI_PATH = "/quick_settings/wifi_action/wifi";
constexpr std::string_view QUICK_DEVELOPER_MODE_PATH = "/quick_settings/developer_mode_action/label";
constexpr std::string_view LAUNCHER_PULL_PATH = "/launcher/pull_hint";
constexpr std::string_view HOME_INTENT_TIMER = "espocket.home_intent";
constexpr int HOME_INTENT_INTERVAL_MS = 50;
constexpr std::string_view STATUS_TIMER = "espocket.status";
constexpr int STATUS_INTERVAL_MS = 30'000;
constexpr int64_t SCREEN_TIMEOUT_US =
    static_cast<int64_t>(CONFIG_ESPOCKET_M6_SCREEN_TIMEOUT_SECONDS) * 1'000'000;

using DisplayHelper = esp_brookesia::service::helper::Display;
using DisplayService = esp_brookesia::service::Display;
using DeviceHelper = esp_brookesia::service::helper::Device;
using SNTPHelper = esp_brookesia::service::helper::SNTP;
using WifiHelper = esp_brookesia::service::helper::Wifi;

constexpr int32_t gesture_exit_distance_px(int32_t height)
{
    return std::clamp<int32_t>(height / 5, 80, 140);
}

constexpr uint16_t gesture_vertical_edge_px(uint32_t height)
{
    return static_cast<uint16_t>(std::clamp<uint32_t>(height * 8U / 100U, 24U, 96U));
}

constexpr uint16_t gesture_horizontal_edge_px(uint32_t width)
{
    return static_cast<uint16_t>(std::clamp<uint32_t>(width * 6U / 100U, 24U, 96U));
}

constexpr bool has_gesture_area(uint8_t value, DisplayHelper::TouchGestureArea area)
{
    return (value & static_cast<uint8_t>(area)) != 0;
}

static_assert(gesture_exit_distance_px(466) == 93);
static_assert(gesture_vertical_edge_px(466) == 37);
static_assert(gesture_horizontal_edge_px(466) == 27);

class LvglLock {
public:
    LvglLock()
        : locked_(esp_lv_adapter_lock(-1) == ESP_OK)
    {}

    ~LvglLock()
    {
        if (locked_) {
            esp_lv_adapter_unlock();
        }
    }

    explicit operator bool() const
    {
        return locked_;
    }

private:
    bool locked_ = false;
};

inline lv_keyboard_mode_t keyboard_mode(std::string_view mode)
{
    if (mode == "number") {
        return LV_KEYBOARD_MODE_NUMBER;
    }
    if (mode == "special") {
        return LV_KEYBOARD_MODE_SPECIAL;
    }
    if (mode == "upper") {
        return LV_KEYBOARD_MODE_TEXT_UPPER;
    }
    return LV_KEYBOARD_MODE_TEXT_LOWER;
}

constexpr std::array<std::string_view, 4> KEYBOARD_MODES = {
    "text", "upper", "number", "special"
};

template <typename Modes>
constexpr bool supports_keyboard_modes(const Modes &allowed_modes)
{
    return allowed_modes.empty() ||
           (allowed_modes.size() == KEYBOARD_MODES.size() &&
            std::ranges::all_of(KEYBOARD_MODES, [&allowed_modes](std::string_view mode) {
                return std::ranges::find(allowed_modes, mode) != allowed_modes.end();
            }));
}

static_assert(supports_keyboard_modes(KEYBOARD_MODES));
static_assert(!supports_keyboard_modes(std::array<std::string_view, 1>{"text"}));

inline std::string make_clock_text()
{
    const auto now = std::chrono::system_clock::now();
    const auto value = std::chrono::system_clock::to_time_t(now);
    std::tm local_time{};
    localtime_r(&value, &local_time);
    char text[6] = {};
    if (std::strftime(text, sizeof(text), "%H:%M", &local_time) == 0) {
        return "--:--";
    }
    return text;
}

inline std::string make_date_text()
{
    const auto now = std::chrono::system_clock::now();
    const auto value = std::chrono::system_clock::to_time_t(now);
    std::tm local_time{};
    localtime_r(&value, &local_time);
    char text[20] = {};
    if (std::strftime(text, sizeof(text), "%a, %b %d", &local_time) == 0) {
        return "Date unavailable";
    }
    return text;
}

// LVGL owns this reference until deletion, including a failed stop/hide.
// Invalidated states reject input; callback userdata cannot outlive its storage.
template<class State>
void retain_overlay_userdata(lv_obj_t *overlay, const std::shared_ptr<State> &state)
{
    auto *retained = new std::shared_ptr<State>(state);
    lv_obj_add_event_cb(overlay, [](lv_event_t *event) {
        if (lv_event_get_target(event) != lv_event_get_current_target(event)) return;
        delete static_cast<std::shared_ptr<State> *>(lv_event_get_user_data(event));
    }, LV_EVENT_DELETE, retained);
}

extern const char shell_gui_json_start[] asm("_binary_shell_gui_json_start");

} // namespace

struct CircularShell::LoadingState {
    std::mutex mutex;
    bool startup = false;
    bool app_wait = false;
    esp_brookesia::system::core::AppId app_id = esp_brookesia::system::core::INVALID_APP_ID;
    lv_obj_t *overlay = nullptr;
    bool invalidated = false;
};

struct CircularShell::KeyboardState {
    std::mutex mutex;
    esp_brookesia::system::core::AppId app_id =
        esp_brookesia::system::core::INVALID_APP_ID;
    esp_brookesia::system::core::KeyboardRequestId request_id =
        esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID;
    lv_obj_t *overlay = nullptr;
    lv_obj_t *text_area = nullptr;
    bool result_pending = false;
    bool confirmed = false;
    bool suspended = false;
    bool invalidated = false;
    std::string text;
};

struct CircularShell::MessageDialogState {
    std::mutex mutex;
    esp_brookesia::system::core::AppId app_id = esp_brookesia::system::core::INVALID_APP_ID;
    esp_brookesia::system::core::MessageDialogRequestId request_id =
        esp_brookesia::system::core::INVALID_MESSAGE_DIALOG_REQUEST_ID;
    lv_obj_t *overlay = nullptr;
    bool result_pending = false;
    int32_t button_index = -1;
    int64_t deadline_us = 0;
    int64_t paused_at_us = -1;
    bool invalidated = false;
    struct Button { MessageDialogState *state; int32_t index; };
    std::array<Button, 3> buttons{{{this, 0}, {this, 1}, {this, 2}}};
};

struct CircularShell::BackOverlayState {
    lv_obj_t *button = nullptr;
    lv_obj_t *card_hint = nullptr;
    std::atomic_bool clicked = false;
};


} // namespace espocket
