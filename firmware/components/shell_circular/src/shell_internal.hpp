#pragma once

#include "shell_overlay_internal.hpp"

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

namespace espocket {
namespace {

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
constexpr std::string_view WATCH_FACE_TIME_PATH = "/watch_face/time";
constexpr std::string_view WATCH_FACE_DATE_PATH = "/watch_face/date";
constexpr std::string_view BATTERY_CARD_PATH = "/battery_card/value";
constexpr std::string_view BRIGHTNESS_CARD_PATH = "/brightness_card/value";
constexpr std::string_view QUICK_BATTERY_PATH = "/quick_settings/battery";
constexpr std::string_view QUICK_BRIGHTNESS_PATH = "/quick_settings/brightness_action/brightness";
constexpr std::string_view QUICK_WIFI_PATH = "/quick_settings/wifi_action/wifi";
constexpr std::string_view QUICK_DEVELOPER_MODE_PATH = "/quick_settings/developer_mode_action/label";

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

extern const char shell_gui_json_start[] asm("_binary_shell_gui_json_start");

} // namespace

} // namespace espocket
