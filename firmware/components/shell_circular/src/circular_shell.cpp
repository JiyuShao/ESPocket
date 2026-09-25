#include "espocket/circular_shell.hpp"

#include <algorithm>
#include <chrono>
#include <cinttypes>
#include <cstdio>
#include <ctime>
#include <string>
#include <utility>

#include "boost/json/object.hpp"
#include "brookesia/lib_utils/describe_helpers.hpp"
#include "brookesia/service_display/service_display.hpp"
#include "brookesia/service_helper/network/sntp.hpp"
#include "brookesia/service_helper/network/wifi.hpp"
#include "brookesia/service_helper/system/device.hpp"
#include "esp_log.h"

namespace espocket {
namespace {

constexpr char SHELL_TAG[] = "ESPocket.Shell";
constexpr char LAUNCHER_TAG[] = "ESPocket.Launcher";
constexpr std::string_view OPEN_PREVIEW_ACTION = "shell.open_preview";
constexpr std::string_view PAGE_FLOW = "shell_pages";
constexpr std::string_view STATUS_TIMER = "espocket.status";
constexpr int STATUS_INTERVAL_MS = 30'000;
constexpr std::string_view CLOCK_PATH = "/overlay/status/clock";
constexpr std::string_view WIFI_PATH = "/overlay/status/wifi";
constexpr std::string_view BATTERY_PATH = "/overlay/status/battery";

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

std::string make_clock_text()
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

constexpr std::string_view SHELL_JSON = R"json({
  "version": "0.1.0",
  "assets": [
    {
      "type": "viewScreen",
      "id": "launcher",
      "commonProps": { "scrollable": false },
      "style": { "bgColor": "#07090d", "padding": 0 },
      "layout": {
        "type": "flex",
        "flexFlow": "column",
        "mainAlign": "center",
        "crossAlign": "center",
        "gap": "24dp"
      },
      "children": [
        {
          "type": "label",
          "id": "brand",
          "labelProps": { "text": "ESPocket" },
          "style": { "textColor": "#f4f7fb", "fontSize": "32sp" },
          "placement": { "width": "220dp", "height": "44dp" }
        },
        {
          "type": "label",
          "id": "caption",
          "labelProps": { "text": "Circular Shell" },
          "style": { "textColor": "#8d98a8", "fontSize": "18sp" },
          "placement": { "width": "220dp", "height": "28dp" }
        },
        {
          "type": "button",
          "id": "shell_preview",
          "events": [ { "type": "clicked", "action": "shell.open_preview" } ],
          "style": { "bgColor": "#2157d5", "radius": "28dp" },
          "placement": { "width": "210dp", "height": "74dp" },
          "children": [
            {
              "type": "label",
              "id": "label",
              "labelProps": { "text": "Shell Preview" },
              "style": { "textColor": "#ffffff", "fontSize": "20sp" },
              "placement": { "mode": "relative", "align": "center" }
            }
          ]
        }
      ]
    },
    {
      "type": "viewScreen",
      "id": "test_page",
      "commonProps": { "scrollable": false },
      "style": { "bgColor": "#101722", "padding": 0 },
      "layout": {
        "type": "flex",
        "flexFlow": "column",
        "mainAlign": "center",
        "crossAlign": "center",
        "gap": "18dp"
      },
      "children": [
        {
          "type": "label",
          "id": "title",
          "labelProps": { "text": "Shell Preview" },
          "style": { "textColor": "#f4f7fb", "fontSize": "32sp" },
          "placement": { "width": "260dp", "height": "44dp" }
        },
        {
          "type": "label",
          "id": "hint",
          "labelProps": { "text": "Swipe up from the bottom edge" },
          "style": { "textColor": "#9ba8ba", "fontSize": "18sp" },
          "placement": { "width": "330dp", "height": "30dp" }
        }
      ]
    },
    {
      "type": "viewScreen",
      "id": "overlay",
      "commonProps": { "clickable": false, "scrollable": false },
      "placement": {
        "mode": "absolute",
        "x": 0,
        "y": 0,
        "width": "${env.widthDp}",
        "height": "${env.heightDp}"
      },
      "style": { "padding": 0 },
      "children": [
        {
          "type": "container",
          "id": "status",
          "commonProps": { "clickable": false, "scrollable": false },
          "style": { "bgColor": "#1c2430", "radius": "29dp", "padding": 0 },
          "placement": {
            "mode": "absolute",
            "x": "105dp",
            "y": "44dp",
            "width": "256dp",
            "height": "58dp"
          },
          "children": [
            {
              "type": "label",
              "id": "wifi",
              "labelProps": { "text": "Wi-Fi: ?" },
              "style": { "textColor": "#aeb9c8", "fontSize": "18sp", "textAlign": "left" },
              "placement": { "mode": "absolute", "x": "14dp", "y": "32dp", "width": "122dp", "height": "22dp" }
            },
            {
              "type": "label",
              "id": "clock",
              "labelProps": { "text": "--:--" },
              "style": { "textColor": "#ffffff", "fontSize": "20sp", "textAlign": "center" },
              "placement": { "mode": "absolute", "x": "80dp", "y": "5dp", "width": "100dp", "height": "25dp" }
            },
            {
              "type": "label",
              "id": "battery",
              "labelProps": { "text": "Bat: ?" },
              "style": { "textColor": "#aeb9c8", "fontSize": "18sp", "textAlign": "right" },
              "placement": { "mode": "absolute", "x": "140dp", "y": "32dp", "width": "102dp", "height": "22dp" }
            }
          ]
        },
        {
          "type": "container",
          "id": "home_indicator",
          "commonProps": { "clickable": false, "scrollable": false },
          "style": { "bgColor": "#e6ebf2", "radius": "3dp", "padding": 0 },
          "placement": {
            "mode": "absolute",
            "x": "191dp",
            "y": "438dp",
            "width": "84dp",
            "height": "6dp"
          }
        }
      ]
    },
    {
      "type": "screenFlow",
      "id": "shell_pages",
      "screens": [ "launcher", "test_page" ],
      "initial": "launcher",
      "transitions": [
        { "from": [], "action": "open_preview", "to": "test_page" },
        { "from": [], "action": "open_launcher", "to": "launcher" }
      ]
    },
    {
      "type": "screenFlow",
      "id": "overlay_flow",
      "screens": [ "overlay" ],
      "initial": "overlay"
    }
  ]
})json";

} // namespace

esp_brookesia::system::core::AppManifest CircularShell::get_manifest() const
{
    esp_brookesia::system::core::AppManifest manifest{};
    manifest.id = "espocket.shell.circular";
    manifest.name = "Circular Shell";
    manifest.localized_names = {
        {"en", "Circular Shell"},
        {"zh_CN", "圆形桌面"},
    };
    manifest.version = "0.1.0";
    manifest.kind = esp_brookesia::system::core::AppKind::Native;
    manifest.visible = false;
    return manifest;
}

esp_brookesia::system::core::AppGuiDescriptor CircularShell::get_gui_descriptor() const
{
    return {
        .root_kind = esp_brookesia::system::core::GuiRootKind::JsonString,
        .root = std::string(SHELL_JSON),
        .resources = {},
        .screen_flows = {
            {
                .screen_flow = std::string(PAGE_FLOW),
                .layer = esp_brookesia::system::core::GuiAppLayer::AppDefault,
            },
            {
                .screen_flow = "overlay_flow",
                .layer = esp_brookesia::system::core::GuiAppLayer::SystemTop,
                .mount_mode = esp_brookesia::gui::MountStackMode::Stack,
            },
        },
    };
}

std::expected<void, std::string> CircularShell::on_start(
    esp_brookesia::system::core::AppContext &context
)
{
    context_ = &context;
    preview_open_ = false;

    auto action_result = context.gui().subscribe_action(OPEN_PREVIEW_ACTION);
    if (!action_result) {
        context_ = nullptr;
        return std::unexpected("Failed to subscribe Launcher action: " + action_result.error());
    }

    auto gesture_result = configure_home_gesture();
    if (!gesture_result) {
        context_ = nullptr;
        return gesture_result;
    }

    start_status();
    ESP_LOGI(SHELL_TAG, "Circular Shell started");
    return {};
}

std::expected<void, std::string> CircularShell::on_stop(
    esp_brookesia::system::core::AppContext &context
)
{
    (void)context;
    stop_status();
    gesture_connection_.disconnect();
    display_binding_.release();
    preview_open_ = false;
    gesture_exit_distance_px_ = 0;
    context_ = nullptr;
    return {};
}

std::expected<void, std::string> CircularShell::on_action(
    esp_brookesia::system::core::AppContext &context,
    std::string_view action
)
{
    (void)context;
    if (action == OPEN_PREVIEW_ACTION) {
        return open_preview();
    }
    return {};
}

std::expected<void, std::string> CircularShell::on_timer(
    esp_brookesia::system::core::AppContext &context,
    esp_brookesia::system::core::TimerId timer_id,
    std::string_view name
)
{
    (void)context;
    if (timer_id == status_timer_id_ && name == STATUS_TIMER) {
        refresh_status();
    }
    return {};
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
    gesture_exit_distance_px_ = gesture_exit_distance_px(static_cast<int32_t>(output->height));
    auto config_result = display.set_touch_gesture_config(output->id, config);
    if (!config_result) {
        return std::unexpected("Failed to configure Home gesture: " + config_result.error());
    }

    gesture_connection_ = display.connect_touch_gesture(
                              output->name,
    [this](const std::string &, const DisplayService::TouchGestureInfo & info) {
        handle_home_gesture(info);
    }
                          );
    if (!gesture_connection_.connected()) {
        return std::unexpected("Failed to subscribe Home gesture events");
    }

    ESP_LOGI(
        SHELL_TAG,
        "Home gesture ready: output=%s exit=%" PRId32 "px edge=%" PRIu16 "px",
        output->name.c_str(),
        gesture_exit_distance_px_,
        config.threshold.vertical_edge
    );
    return {};
}

void CircularShell::handle_home_gesture(const DisplayHelper::TouchGestureInfo &info)
{
    if (context_ == nullptr || !preview_open_) {
        return;
    }
    if (info.event_type != DisplayHelper::TouchGestureEventType::Pressing ||
            !has_gesture_area(info.start_area, DisplayHelper::TouchGestureArea::BottomEdge)) {
        return;
    }

    const auto upward_distance = std::max(0, info.start_y - info.stop_y);
    if (upward_distance < gesture_exit_distance_px_ &&
            info.direction != DisplayHelper::TouchGestureDirection::Up) {
        return;
    }
    if (upward_distance < gesture_exit_distance_px_) {
        return;
    }

    auto result = open_launcher();
    if (!result) {
        ESP_LOGW(SHELL_TAG, "Home gesture failed: %s", result.error().c_str());
    }
}

std::expected<void, std::string> CircularShell::open_preview()
{
    if (context_ == nullptr) {
        return std::unexpected("Circular Shell is not running");
    }
    auto result = context_->gui().trigger_screen_flow(PAGE_FLOW, "open_preview");
    if (!result) {
        return result;
    }
    preview_open_ = true;
    ESP_LOGI(LAUNCHER_TAG, "Opened Shell Preview");
    return {};
}

std::expected<void, std::string> CircularShell::open_launcher()
{
    if (context_ == nullptr) {
        return std::unexpected("Circular Shell is not running");
    }
    auto result = context_->gui().trigger_screen_flow(PAGE_FLOW, "open_launcher");
    if (!result) {
        return result;
    }
    preview_open_ = false;
    ESP_LOGI(LAUNCHER_TAG, "Home intent opened Launcher");
    return {};
}

void CircularShell::start_status()
{
    set_status_text(CLOCK_PATH, "--:--");
    set_status_text(WIFI_PATH, "Wi-Fi: ?");
    set_status_text(BATTERY_PATH, "Bat: ?");

    auto &manager = esp_brookesia::service::ServiceManager::get_instance();

    if (WifiHelper::is_available()) {
        wifi_binding_ = manager.bind(WifiHelper::get_name().data());
        if (wifi_binding_.is_valid()) {
            wifi_connection_ = WifiHelper::subscribe_event(
                                   WifiHelper::EventId::GeneralEventHappened,
            [this](const std::string &, const std::string & event, bool unexpected) {
                if (unexpected) {
                    ESP_LOGW(SHELL_TAG, "Wi-Fi reported unexpected event: %s", event.c_str());
                }
                if (event == "Connected") {
                    set_status_text(WIFI_PATH, "Wi-Fi: linked");
                } else if (event == "Deinited" || event == "Inited" || event == "Stopped" ||
                           event == "Started" || event == "Disconnected") {
                    set_status_text(WIFI_PATH, "Wi-Fi: no link");
                } else {
                    set_status_text(WIFI_PATH, "Wi-Fi: ?");
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
            [this](const std::string &, const esp_brookesia::service::EventItemMap & items) {
                auto item = items.find("State");
                if (item == items.end() || !std::holds_alternative<boost::json::object>(item->second)) {
                    set_status_text(BATTERY_PATH, "Bat: ?");
                    return;
                }
                DeviceHelper::PowerBatteryState state;
                if (!BROOKESIA_DESCRIBE_FROM_JSON(std::get<boost::json::object>(item->second), state) ||
                        !state.is_present || !state.percentage.has_value()) {
                    set_status_text(BATTERY_PATH, "Bat: ?");
                    return;
                }
                set_status_text(BATTERY_PATH, "Bat: " + std::to_string(*state.percentage) + "%");
            }
                                  );
        }
    }

    if (SNTPHelper::is_available()) {
        sntp_binding_ = manager.bind(SNTPHelper::get_name().data());
        if (sntp_binding_.is_valid()) {
            sntp_state_connection_ = SNTPHelper::subscribe_event(
                                         SNTPHelper::EventId::StateChanged,
            [this](const std::string &, const std::string &) {
                refresh_clock();
            }
                                     );
            sntp_timezone_connection_ = SNTPHelper::subscribe_event(
                                            SNTPHelper::EventId::TimezoneChanged,
            [this](const std::string &, const std::string &) {
                refresh_clock();
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
    wifi_binding_.release();
    device_binding_.release();
    sntp_binding_.release();
}

void CircularShell::refresh_status()
{
    refresh_clock();
    refresh_wifi();
    refresh_battery();
}

void CircularShell::refresh_clock()
{
    std::string text = "--:--";
    if (sntp_binding_.is_valid()) {
        auto synced = SNTPHelper::call_function_sync<bool>(SNTPHelper::FunctionId::IsTimeSynced);
        if (synced && *synced) {
            text = make_clock_text();
        }
    }
    set_status_text(CLOCK_PATH, std::move(text));
}

void CircularShell::refresh_wifi()
{
    if (!wifi_binding_.is_valid()) {
        set_status_text(WIFI_PATH, "Wi-Fi: ?");
        return;
    }
    auto state = WifiHelper::call_function_sync<std::string>(WifiHelper::FunctionId::GetGeneralState);
    if (!state) {
        set_status_text(WIFI_PATH, "Wi-Fi: ?");
    } else if (*state == "Connected") {
        set_status_text(WIFI_PATH, "Wi-Fi: linked");
    } else if (*state == "Idle" || *state == "Initing" || *state == "Inited" || *state == "Deiniting" ||
               *state == "Starting" || *state == "Started" || *state == "Stopping" ||
               *state == "Connecting" || *state == "Disconnecting") {
        set_status_text(WIFI_PATH, "Wi-Fi: no link");
    } else {
        set_status_text(WIFI_PATH, "Wi-Fi: ?");
    }
}

void CircularShell::refresh_battery()
{
    if (!device_binding_.is_valid()) {
        set_status_text(BATTERY_PATH, "Bat: ?");
        return;
    }
    auto value = DeviceHelper::call_function_sync<boost::json::object>(
                     DeviceHelper::FunctionId::GetPowerBatteryState
                 );
    DeviceHelper::PowerBatteryState state;
    if (!value || !BROOKESIA_DESCRIBE_FROM_JSON(*value, state) || !state.is_present ||
            !state.percentage.has_value()) {
        set_status_text(BATTERY_PATH, "Bat: ?");
        return;
    }
    set_status_text(BATTERY_PATH, "Bat: " + std::to_string(*state.percentage) + "%");
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
