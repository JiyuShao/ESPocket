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

constexpr char SHELL_TAG[] = "ESPocket.Shell";
constexpr char LAUNCHER_TAG[] = "ESPocket.Launcher";
constexpr std::string_view HELLO_NATIVE_MANIFEST_ID = "espocket.app.hello";
constexpr std::string_view HELLO_RUNTIME_MANIFEST_ID = "espocket.app.hello_runtime";
constexpr std::string_view SETTINGS_MANIFEST_ID = "brookesia.general.settings";
constexpr std::string_view APP_STORE_MANIFEST_ID = "brookesia.general.app_store";
constexpr std::string_view OPEN_HELLO_NATIVE_ACTION = "shell.open_hello_native";
constexpr std::string_view OPEN_HELLO_RUNTIME_ACTION = "shell.open_hello_runtime";
constexpr std::string_view OPEN_SETTINGS_ACTION = "shell.open_settings";
constexpr std::string_view OPEN_APP_STORE_ACTION = "shell.open_app_store";
constexpr std::string_view STEP_BRIGHTNESS_ACTION = "shell.step_brightness";
constexpr std::string_view TOGGLE_WIFI_ACTION = "shell.toggle_wifi";
constexpr std::string_view PAGE_FLOW = "shell_pages";
constexpr std::string_view WATCH_FACE_TIME_PATH = "/watch_face/time";
constexpr std::string_view WATCH_FACE_DATE_PATH = "/watch_face/date";
constexpr std::string_view BATTERY_CARD_PATH = "/battery_card/value";
constexpr std::string_view BRIGHTNESS_CARD_PATH = "/brightness_card/value";
constexpr std::string_view QUICK_BATTERY_PATH = "/quick_settings/battery";
constexpr std::string_view QUICK_BRIGHTNESS_PATH = "/quick_settings/brightness_action/brightness";
constexpr std::string_view QUICK_WIFI_PATH = "/quick_settings/wifi_action/wifi";
constexpr std::string_view HOME_INTENT_TIMER = "espocket.home_intent";
constexpr int HOME_INTENT_INTERVAL_MS = 50;
constexpr std::string_view STATUS_TIMER = "espocket.status";
constexpr int STATUS_INTERVAL_MS = 30'000;
constexpr std::string_view WIFI_PATH = "/overlay/status/wifi";
constexpr std::string_view BATTERY_PATH = "/overlay/status/battery";
constexpr int64_t SCREEN_TIMEOUT_US =
    static_cast<int64_t>(CONFIG_ESPOCKET_M6_SCREEN_TIMEOUT_SECONDS) * 1'000'000;

enum class GestureIntent : uint8_t {
    None,
    WatchFace,
    BatteryCard,
    BrightnessCard,
    QuickSettings,
    Launcher,
    Back,
};

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

lv_keyboard_mode_t keyboard_mode(std::string_view mode)
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

std::string make_date_text()
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

constexpr std::string_view SHELL_JSON = R"json({
  "version": "0.1.0",
  "assets": [
    {
      "type": "viewScreen",
      "id": "watch_face",
      "commonProps": { "scrollable": false },
      "style": { "bgColor": "#070a10", "padding": 0 },
      "layout": {
        "type": "flex",
        "flexFlow": "column",
        "mainAlign": "center",
        "crossAlign": "center",
        "gap": "10dp"
      },
      "children": [
        {
          "type": "label",
          "id": "eyebrow",
          "labelProps": { "text": "LOCAL TIME" },
          "style": { "textColor": "#718096", "fontSize": "14sp", "textAlign": "center" },
          "placement": { "width": "220dp", "height": "22dp" }
        },
        {
          "type": "label",
          "id": "time",
          "labelProps": { "text": "--:--" },
          "style": { "textColor": "#f8fafc", "fontSize": "76sp", "textAlign": "center" },
          "placement": { "width": "340dp", "height": "100dp" }
        },
        {
          "type": "label",
          "id": "date",
          "labelProps": { "text": "Waiting for sync" },
          "style": { "textColor": "#cbd5e1", "fontSize": "20sp", "textAlign": "center" },
          "placement": { "width": "280dp", "height": "32dp" }
        },
        {
          "type": "container",
          "id": "accent",
          "commonProps": { "clickable": false, "scrollable": false },
          "style": { "bgColor": "#2dd4bf", "radius": "2dp", "padding": 0 },
          "placement": { "width": "38dp", "height": "4dp" }
        },
        {
          "type": "label",
          "id": "launcher_hint",
          "labelProps": { "text": "APPS" },
          "style": { "textColor": "#64748b", "fontSize": "14sp", "textAlign": "center" },
          "placement": { "width": "160dp", "height": "22dp" }
        }
      ]
    },
    {
      "type": "viewScreen",
      "id": "battery_card",
      "commonProps": { "scrollable": false },
      "style": { "bgColor": "#10251e", "padding": 0 },
      "layout": { "type": "flex", "flexFlow": "column", "mainAlign": "center", "crossAlign": "center", "gap": "18dp" },
      "children": [
        { "type": "label", "id": "title", "labelProps": { "text": "Battery" }, "style": { "textColor": "#9ae6b4", "fontSize": "28sp" }, "placement": { "width": "250dp", "height": "40dp" } },
        { "type": "label", "id": "value", "labelProps": { "text": "Battery: ?" }, "style": { "textColor": "#ffffff", "fontSize": "40sp", "textAlign": "center" }, "placement": { "width": "300dp", "height": "58dp" } },
        { "type": "label", "id": "hint", "labelProps": { "text": "Read only · swipe left for Home" }, "style": { "textColor": "#86a89b", "fontSize": "15sp", "textAlign": "center" }, "placement": { "width": "300dp", "height": "26dp" } }
      ]
    },
    {
      "type": "viewScreen",
      "id": "brightness_card",
      "commonProps": { "scrollable": false },
      "style": { "bgColor": "#261c0b", "padding": 0 },
      "layout": { "type": "flex", "flexFlow": "column", "mainAlign": "center", "crossAlign": "center", "gap": "14dp" },
      "children": [
        { "type": "label", "id": "title", "labelProps": { "text": "Brightness" }, "style": { "textColor": "#fbd38d", "fontSize": "28sp" }, "placement": { "width": "250dp", "height": "40dp" } },
        { "type": "label", "id": "value", "labelProps": { "text": "Brightness: ?" }, "style": { "textColor": "#ffffff", "fontSize": "28sp", "textAlign": "center" }, "placement": { "width": "300dp", "height": "44dp" } },
        { "type": "button", "id": "step", "events": [ { "type": "clicked", "action": "shell.step_brightness" } ], "style": { "bgColor": "#c47c14", "radius": "26dp" }, "placement": { "width": "220dp", "height": "58dp" }, "children": [ { "type": "label", "id": "label", "labelProps": { "text": "Increase 20%" }, "style": { "textColor": "#ffffff", "fontSize": "18sp" }, "placement": { "mode": "relative", "align": "center" } } ] },
        { "type": "button", "id": "settings", "events": [ { "type": "clicked", "action": "shell.open_settings" } ], "style": { "bgColor": "#725018", "radius": "22dp" }, "placement": { "width": "180dp", "height": "46dp" }, "children": [ { "type": "label", "id": "label", "labelProps": { "text": "Display Settings" }, "style": { "textColor": "#ffffff", "fontSize": "16sp" }, "placement": { "mode": "relative", "align": "center" } } ] }
      ]
    },
    {
      "type": "viewScreen",
      "id": "quick_settings",
      "commonProps": { "scrollable": false },
      "style": { "bgColor": "#111827", "padding": 0 },
      "layout": { "type": "flex", "flexFlow": "column", "mainAlign": "center", "crossAlign": "center", "gap": "10dp" },
      "children": [
        { "type": "label", "id": "title", "labelProps": { "text": "Quick Settings" }, "style": { "textColor": "#ffffff", "fontSize": "26sp" }, "placement": { "width": "280dp", "height": "38dp" } },
        { "type": "label", "id": "battery", "labelProps": { "text": "Battery: ?" }, "style": { "textColor": "#aeb9c8", "fontSize": "17sp" }, "placement": { "width": "250dp", "height": "26dp" } },
        { "type": "button", "id": "brightness_action", "events": [ { "type": "clicked", "action": "shell.step_brightness" } ], "style": { "bgColor": "#b7791f", "radius": "24dp" }, "placement": { "width": "230dp", "height": "52dp" }, "children": [ { "type": "label", "id": "brightness", "labelProps": { "text": "Brightness: ?" }, "style": { "textColor": "#ffffff", "fontSize": "17sp" }, "placement": { "mode": "relative", "align": "center" } } ] },
        { "type": "button", "id": "wifi_action", "events": [ { "type": "clicked", "action": "shell.toggle_wifi" } ], "style": { "bgColor": "#2563a9", "radius": "24dp" }, "placement": { "width": "230dp", "height": "52dp" }, "children": [ { "type": "label", "id": "wifi", "labelProps": { "text": "Wi-Fi: ?" }, "style": { "textColor": "#ffffff", "fontSize": "17sp" }, "placement": { "mode": "relative", "align": "center" } } ] },
        { "type": "button", "id": "settings", "events": [ { "type": "clicked", "action": "shell.open_settings" } ], "style": { "bgColor": "#277b65", "radius": "24dp" }, "placement": { "width": "230dp", "height": "52dp" }, "children": [ { "type": "label", "id": "label", "labelProps": { "text": "Open Settings" }, "style": { "textColor": "#ffffff", "fontSize": "17sp" }, "placement": { "mode": "relative", "align": "center" } } ] }
      ]
    },
    {
      "type": "viewScreen",
      "id": "launcher",
      "commonProps": { "scrollable": false },
      "style": { "bgColor": "#070a10", "padding": 0 },
      "layout": {
        "type": "flex",
        "flexFlow": "column",
        "mainAlign": "center",
        "crossAlign": "center",
        "gap": "8dp"
      },
      "children": [
        {
          "type": "label",
          "id": "title",
          "labelProps": { "text": "Apps" },
          "style": { "textColor": "#f8fafc", "fontSize": "34sp", "textAlign": "center" },
          "placement": { "width": "220dp", "height": "44dp" }
        },
        {
          "type": "label",
          "id": "caption",
          "labelProps": { "text": "ESPocket" },
          "style": { "textColor": "#64748b", "fontSize": "15sp", "textAlign": "center" },
          "placement": { "width": "220dp", "height": "22dp" }
        },
        {
          "type": "container",
          "id": "app_row_primary",
          "commonProps": { "scrollable": false },
          "layout": { "type": "flex", "flexFlow": "row", "mainAlign": "spaceBetween", "crossAlign": "center" },
          "style": { "padding": 0 },
          "placement": { "width": "294dp", "height": "90dp" },
          "children": [
            {
              "type": "button",
              "id": "hello_native",
              "events": [ { "type": "clicked", "action": "shell.open_hello_native" } ],
              "style": { "bgColor": "#1d4ed8", "radius": "30dp" },
              "placement": { "width": "142dp", "height": "90dp" },
              "children": [ { "type": "label", "id": "label", "labelProps": { "text": "Native" }, "style": { "textColor": "#ffffff", "fontSize": "18sp" }, "placement": { "mode": "relative", "align": "center" } } ]
            },
            {
              "type": "button",
              "id": "hello_runtime",
              "events": [ { "type": "clicked", "action": "shell.open_hello_runtime" } ],
              "style": { "bgColor": "#6d28d9", "radius": "30dp" },
              "placement": { "width": "142dp", "height": "90dp" },
              "children": [ { "type": "label", "id": "label", "labelProps": { "text": "Runtime" }, "style": { "textColor": "#ffffff", "fontSize": "18sp" }, "placement": { "mode": "relative", "align": "center" } } ]
            }
          ]
        },
        {
          "type": "container",
          "id": "app_row_system",
          "commonProps": { "scrollable": false },
          "layout": { "type": "flex", "flexFlow": "row", "mainAlign": "spaceBetween", "crossAlign": "center" },
          "style": { "padding": 0 },
          "placement": { "width": "294dp", "height": "90dp" },
          "children": [
            {
              "type": "button",
              "id": "settings",
              "events": [ { "type": "clicked", "action": "shell.open_settings" } ],
              "style": { "bgColor": "#0f766e", "radius": "30dp" },
              "placement": { "width": "142dp", "height": "90dp" },
              "children": [ { "type": "label", "id": "label", "labelProps": { "text": "Settings" }, "style": { "textColor": "#ffffff", "fontSize": "17sp" }, "placement": { "mode": "relative", "align": "center" } } ]
            },
            {
              "type": "button",
              "id": "app_store",
              "events": [ { "type": "clicked", "action": "shell.open_app_store" } ],
              "style": { "bgColor": "#9a5a16", "radius": "30dp" },
              "placement": { "width": "142dp", "height": "90dp" },
              "children": [ { "type": "label", "id": "label", "labelProps": { "text": "Store" }, "style": { "textColor": "#ffffff", "fontSize": "18sp" }, "placement": { "mode": "relative", "align": "center" } } ]
            }
          ]
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
          "style": { "bgColor": "#111827", "radius": "21dp", "padding": 0 },
          "placement": {
            "mode": "absolute",
            "x": "113dp",
            "y": "42dp",
            "width": "240dp",
            "height": "42dp"
          },
          "children": [
            {
              "type": "label",
              "id": "wifi",
              "labelProps": { "text": "Wi-Fi: ?" },
              "style": { "textColor": "#94a3b8", "fontSize": "15sp", "textAlign": "left" },
              "placement": { "mode": "absolute", "x": "14dp", "y": "10dp", "width": "112dp", "height": "22dp" }
            },
            {
              "type": "label",
              "id": "battery",
              "labelProps": { "text": "Bat: ?" },
              "style": { "textColor": "#94a3b8", "fontSize": "15sp", "textAlign": "right" },
              "placement": { "mode": "absolute", "x": "126dp", "y": "10dp", "width": "100dp", "height": "22dp" }
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
            "x": "201dp",
            "y": "439dp",
            "width": "64dp",
            "height": "6dp"
          }
        }
      ]
    },
    {
      "type": "screenFlow",
      "id": "shell_pages",
      "screens": [ "watch_face", "battery_card", "brightness_card", "quick_settings", "launcher" ],
      "initial": "watch_face",
      "transitions": [
        { "from": [], "action": "open_watch_face", "to": "watch_face" },
        { "from": [], "action": "open_battery_card", "to": "battery_card" },
        { "from": [], "action": "open_brightness_card", "to": "brightness_card" },
        { "from": [], "action": "open_quick_settings", "to": "quick_settings" },
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
    std::string text;
};

CircularShell::CircularShell(
    PowerPressCountProvider power_press_count_provider,
    DisplayOnProvider display_on_provider,
    AppVisibleProvider app_visible_provider,
    SystemHandler power_handler,
    SystemHandler screen_timeout_handler,
    AppLaunchHandler app_launch_handler,
    SystemHandler back_handler,
    KeyboardResultHandler keyboard_result_handler
)
    : power_press_count_provider_(std::move(power_press_count_provider)),
      display_on_provider_(std::move(display_on_provider)),
      app_visible_provider_(std::move(app_visible_provider)),
      power_handler_(std::move(power_handler)),
      screen_timeout_handler_(std::move(screen_timeout_handler)),
      app_launch_handler_(std::move(app_launch_handler)),
      back_handler_(std::move(back_handler)),
      keyboard_result_handler_(std::move(keyboard_result_handler))
{}

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
    keyboard_state_ = std::make_shared<KeyboardState>();

    for (const auto action : {
             OPEN_HELLO_NATIVE_ACTION,
             OPEN_HELLO_RUNTIME_ACTION,
             OPEN_SETTINGS_ACTION,
             OPEN_APP_STORE_ACTION,
             STEP_BRIGHTNESS_ACTION,
             TOGGLE_WIFI_ACTION,
         }) {
        auto action_result = context.gui().subscribe_action(action);
        if (!action_result) {
            keyboard_state_.reset();
            context_ = nullptr;
            return std::unexpected("Failed to subscribe Launcher action: " + action_result.error());
        }
    }

    home_gesture_state_ = std::make_shared<HomeGestureState>();
    last_power_press_count_ = power_press_count_provider_ ? power_press_count_provider_() : 0;
    last_activity_generation_ = 0;
    last_activity_us_ = esp_timer_get_time();
    screen_timeout_latched_ = false;
    auto gesture_result = configure_home_gesture();
    if (!gesture_result) {
        home_gesture_state_.reset();
        keyboard_state_.reset();
        context_ = nullptr;
        return gesture_result;
    }

    auto home_timer = context.timer().start_periodic(
                          HOME_INTENT_TIMER,
                          HOME_INTENT_INTERVAL_MS
                      );
    if (!home_timer) {
        gesture_connection_.disconnect();
        display_binding_.release();
        home_gesture_state_.reset();
        keyboard_state_.reset();
        context_ = nullptr;
        return std::unexpected(
            "Failed to start Home intent timer: " + home_timer.error()
        );
    }
    home_intent_timer_id_ = *home_timer;

    callback_state_ = std::make_shared<CallbackState>();
    callback_state_->owner = this;
    start_status();
    ESP_LOGI(SHELL_TAG, "Circular Shell started");
    return {};
}

std::expected<void, std::string> CircularShell::on_stop(
    esp_brookesia::system::core::AppContext &context
)
{
    (void)context;
    if (keyboard_state_) {
        esp_brookesia::system::core::AppId app_id =
            esp_brookesia::system::core::INVALID_APP_ID;
        esp_brookesia::system::core::KeyboardRequestId request_id =
            esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID;
        {
            std::lock_guard lock(keyboard_state_->mutex);
            app_id = keyboard_state_->app_id;
            request_id = keyboard_state_->request_id;
        }
        if (request_id != esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID) {
            hide_keyboard(app_id, request_id);
        }
    }
    gesture_connection_.disconnect();
    if (home_intent_timer_id_ != esp_brookesia::system::core::INVALID_TIMER_ID) {
        (void)context.timer().stop(home_intent_timer_id_);
    }
    home_intent_timer_id_ = esp_brookesia::system::core::INVALID_TIMER_ID;
    home_gesture_state_.reset();
    stop_status();
    display_binding_.release();
    context_ = nullptr;
    keyboard_state_.reset();
    callback_state_.reset();
    return {};
}

std::expected<void, std::string> CircularShell::on_action(
    esp_brookesia::system::core::AppContext &context,
    std::string_view action
)
{
    (void)context;
    if (action == OPEN_HELLO_NATIVE_ACTION) {
        return open_app(HELLO_NATIVE_MANIFEST_ID, "Hello Native");
    }
    if (action == OPEN_HELLO_RUNTIME_ACTION) {
        return open_app(HELLO_RUNTIME_MANIFEST_ID, "Hello Runtime");
    }
    if (action == OPEN_SETTINGS_ACTION) {
        return open_app(SETTINGS_MANIFEST_ID, "Settings");
    }
    if (action == OPEN_APP_STORE_ACTION) {
        return open_app(APP_STORE_MANIFEST_ID, "App Store");
    }
    if (action == STEP_BRIGHTNESS_ACTION) {
        return step_brightness();
    }
    if (action == TOGGLE_WIFI_ACTION) {
        return toggle_wifi();
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
    if (timer_id == home_intent_timer_id_ && name == HOME_INTENT_TIMER) {
        if (keyboard_state_ && keyboard_result_handler_) {
            esp_brookesia::system::core::AppId app_id =
                esp_brookesia::system::core::INVALID_APP_ID;
            esp_brookesia::system::core::KeyboardRequestId request_id =
                esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID;
            bool confirmed = false;
            std::string text;
            {
                std::lock_guard lock(keyboard_state_->mutex);
                if (keyboard_state_->result_pending) {
                    app_id = keyboard_state_->app_id;
                    request_id = keyboard_state_->request_id;
                    confirmed = keyboard_state_->confirmed;
                    text = std::move(keyboard_state_->text);
                    keyboard_state_->result_pending = false;
                }
            }
            if (request_id != esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID) {
                hide_keyboard(app_id, request_id);
                keyboard_result_handler_(app_id, request_id, confirmed, std::move(text));
            }
        }
        if (power_press_count_provider_ && power_handler_) {
            const auto count = power_press_count_provider_();
            if (count != last_power_press_count_) {
                last_power_press_count_ = count;
                power_handler_();
            }
        }
        if (home_gesture_state_) {
            const auto activity = home_gesture_state_->activity_generation.load(std::memory_order_acquire);
            if (activity != last_activity_generation_) {
                last_activity_generation_ = activity;
                last_activity_us_ = esp_timer_get_time();
                screen_timeout_latched_ = false;
            }
            const auto intent = static_cast<GestureIntent>(
                                    home_gesture_state_->pending_gesture.exchange(
                                        static_cast<uint8_t>(GestureIntent::None),
                                        std::memory_order_acq_rel
                                    )
                                );
            std::expected<void, std::string> result{};
            switch (intent) {
            case GestureIntent::WatchFace:
                result = show_surface(ShellSurface::WatchFace);
                break;
            case GestureIntent::BatteryCard:
                result = show_surface(ShellSurface::BatteryCard);
                break;
            case GestureIntent::BrightnessCard:
                result = show_surface(ShellSurface::BrightnessCard);
                break;
            case GestureIntent::QuickSettings:
                result = show_surface(ShellSurface::QuickSettings);
                break;
            case GestureIntent::Launcher:
                result = show_surface(ShellSurface::Launcher);
                break;
            case GestureIntent::Back:
                if (back_handler_) {
                    back_handler_();
                }
                break;
            case GestureIntent::None:
                break;
            }
            if (!result) {
                ESP_LOGW(SHELL_TAG, "Failed to handle navigation gesture: %s", result.error().c_str());
            }
        }
        const bool display_on = !display_on_provider_ || display_on_provider_();
        if (display_on && !screen_timeout_latched_ && SCREEN_TIMEOUT_US > 0 &&
                esp_timer_get_time() - last_activity_us_ >= SCREEN_TIMEOUT_US) {
            screen_timeout_latched_ = true;
            if (screen_timeout_handler_) {
                screen_timeout_handler_();
            }
        }
        return {};
    }
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
    const auto exit_distance_px = gesture_exit_distance_px(static_cast<int32_t>(output->height));
    auto config_result = display.set_touch_gesture_config(output->id, config);
    if (!config_result) {
        return std::unexpected("Failed to configure Home gesture: " + config_result.error());
    }

    gesture_connection_ = display.connect_touch_gesture(
                              output->name,
    [exit_distance_px,
     state = home_gesture_state_,
     display_on_provider = display_on_provider_,
     app_visible_provider = app_visible_provider_](
        const std::string &, const DisplayService::TouchGestureInfo &info
    ) {
        if (info.event_type == DisplayHelper::TouchGestureEventType::Press) {
            state->consumed.store(false, std::memory_order_release);
            if (display_on_provider && !display_on_provider()) {
                return;
            }
            state->activity_generation.fetch_add(1, std::memory_order_acq_rel);
            return;
        }
        if (info.event_type == DisplayHelper::TouchGestureEventType::Release) {
            state->consumed.store(false, std::memory_order_release);
            return;
        }
        if (info.event_type != DisplayHelper::TouchGestureEventType::Pressing ||
                (display_on_provider && !display_on_provider()) ||
                info.distance_px < exit_distance_px) {
            return;
        }

        GestureIntent intent = GestureIntent::None;
        const bool edge_back =
            (has_gesture_area(info.start_area, DisplayHelper::TouchGestureArea::LeftEdge) &&
             info.direction == DisplayHelper::TouchGestureDirection::Right) ||
            (has_gesture_area(info.start_area, DisplayHelper::TouchGestureArea::RightEdge) &&
             info.direction == DisplayHelper::TouchGestureDirection::Left);
        if (edge_back) {
            intent = GestureIntent::Back;
        } else if (!app_visible_provider || !app_visible_provider()) {
            switch (state->surface.load(std::memory_order_acquire)) {
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

    if (!app_launch_handler_) {
        return std::unexpected("System app launch handler is unavailable");
    }
    const auto source = current_surface();
    auto result = app_launch_handler_(manifest_id, source);
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

std::expected<void, std::string> CircularShell::show_keyboard(
    esp_brookesia::system::core::AppId app_id,
    esp_brookesia::system::core::KeyboardRequestId request_id,
    const esp_brookesia::system::core::KeyboardRequestOptions &options
)
{
    if (context_ == nullptr || !keyboard_state_) {
        return std::unexpected("Circular Shell is not running");
    }
    if (std::ranges::find(KEYBOARD_MODES, options.mode) == KEYBOARD_MODES.end()) {
        return std::unexpected("Unsupported keyboard mode: " + options.mode);
    }
    if (!supports_keyboard_modes(options.allowed_modes)) {
        return std::unexpected("Restricted keyboard mode sets are not supported");
    }
    if (options.max_length < 0) {
        return std::unexpected("Keyboard max_length must not be negative");
    }

    LvglLock lvgl_lock;
    if (!lvgl_lock) {
        return std::unexpected("Failed to lock LVGL for keyboard");
    }

    std::lock_guard state_lock(keyboard_state_->mutex);
    if (keyboard_state_->request_id !=
            esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID) {
        return std::unexpected("Another keyboard request is already active");
    }

    auto *overlay = lv_obj_create(lv_layer_top());
    if (overlay == nullptr) {
        return std::unexpected("Failed to create keyboard overlay");
    }
    lv_obj_remove_flag(overlay, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_size(overlay, lv_pct(100), lv_pct(100));
    lv_obj_center(overlay);
    lv_obj_set_style_bg_color(overlay, lv_color_hex(0x07090d), 0);
    lv_obj_set_style_bg_opa(overlay, LV_OPA_COVER, 0);
    lv_obj_set_style_border_width(overlay, 0, 0);
    lv_obj_set_style_radius(overlay, 0, 0);
    lv_obj_set_style_pad_all(overlay, 0, 0);

    auto *title = lv_label_create(overlay);
    auto *text_area = lv_textarea_create(overlay);
    auto *keyboard = lv_keyboard_create(overlay);
    if (title == nullptr || text_area == nullptr || keyboard == nullptr) {
        lv_obj_delete(overlay);
        return std::unexpected("Failed to create keyboard controls");
    }

    lv_label_set_text(title, options.title.empty() ? "Enter text" : options.title.c_str());
    lv_label_set_long_mode(title, LV_LABEL_LONG_MODE_DOTS);
    lv_obj_set_size(title, 330, 28);
    lv_obj_align(title, LV_ALIGN_TOP_MID, 0, 52);
    lv_obj_set_style_text_color(title, lv_color_hex(0xf4f7fb), 0);
    lv_obj_set_style_text_font(title, &lv_font_montserrat_20, 0);
    lv_obj_set_style_text_align(title, LV_TEXT_ALIGN_CENTER, 0);

    lv_textarea_set_one_line(text_area, true);
    lv_textarea_set_password_mode(text_area, options.password);
    if (options.password) {
        lv_textarea_set_password_show_time(text_area, 0);
    }
    if (options.max_length > 0) {
        lv_textarea_set_max_length(text_area, static_cast<uint32_t>(options.max_length));
    }
    lv_textarea_set_text(text_area, options.initial_text.c_str());
    lv_textarea_set_placeholder_text(text_area, options.placeholder.c_str());
    lv_obj_set_size(text_area, 330, 54);
    lv_obj_align(text_area, LV_ALIGN_TOP_MID, 0, 94);
    lv_obj_set_style_bg_color(text_area, lv_color_hex(0x18212f), 0);
    lv_obj_set_style_bg_opa(text_area, LV_OPA_COVER, 0);
    lv_obj_set_style_border_color(text_area, lv_color_hex(0x50627a), 0);
    lv_obj_set_style_border_width(text_area, 2, 0);
    lv_obj_set_style_radius(text_area, 16, 0);
    lv_obj_set_style_text_color(text_area, lv_color_hex(0xffffff), 0);
    lv_obj_set_style_text_color(
        text_area,
        lv_color_hex(0x8d98a8),
        LV_PART_TEXTAREA_PLACEHOLDER
    );
    lv_obj_set_style_text_font(text_area, &lv_font_montserrat_20, 0);

    lv_keyboard_set_textarea(keyboard, text_area);
    lv_keyboard_set_mode(keyboard, keyboard_mode(options.mode));
    lv_keyboard_set_popovers(keyboard, false);
    lv_obj_set_size(keyboard, 330, 220);
    lv_obj_align(keyboard, LV_ALIGN_BOTTOM_MID, 0, -68);
    lv_obj_set_style_bg_color(keyboard, lv_color_hex(0x18212f), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(keyboard, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_bg_color(keyboard, lv_color_hex(0x31405a), LV_PART_ITEMS);
    lv_obj_set_style_bg_color(
        keyboard,
        lv_color_hex(0x2157d5),
        static_cast<lv_style_selector_t>(
            static_cast<uint32_t>(LV_PART_ITEMS) |
            static_cast<uint32_t>(LV_STATE_PRESSED)
        )
    );
    lv_obj_set_style_text_color(keyboard, lv_color_hex(0xffffff), LV_PART_ITEMS);
    lv_obj_set_style_text_font(keyboard, &lv_font_montserrat_18, LV_PART_ITEMS);
    lv_obj_set_style_radius(keyboard, 8, LV_PART_ITEMS);

    keyboard_state_->app_id = app_id;
    keyboard_state_->request_id = request_id;
    keyboard_state_->overlay = overlay;
    keyboard_state_->text_area = text_area;
    keyboard_state_->result_pending = false;
    keyboard_state_->confirmed = false;
    keyboard_state_->text.clear();

    auto keyboard_event = [](lv_event_t *event) {
        auto *state = static_cast<KeyboardState *>(lv_event_get_user_data(event));
        if (state == nullptr) {
            return;
        }
        std::lock_guard lock(state->mutex);
        if (state->request_id ==
                esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID ||
                state->result_pending) {
            return;
        }
        state->confirmed = lv_event_get_code(event) == LV_EVENT_READY;
        state->text = state->confirmed && state->text_area != nullptr ?
                      lv_textarea_get_text(state->text_area) : "";
        state->result_pending = true;
    };
    lv_obj_add_event_cb(keyboard, keyboard_event, LV_EVENT_READY, keyboard_state_.get());
    lv_obj_add_event_cb(keyboard, keyboard_event, LV_EVENT_CANCEL, keyboard_state_.get());
    lv_obj_add_state(text_area, LV_STATE_FOCUSED);

    ESP_LOGI(SHELL_TAG, "System keyboard opened");
    return {};
}

void CircularShell::hide_keyboard(
    esp_brookesia::system::core::AppId app_id,
    esp_brookesia::system::core::KeyboardRequestId request_id
)
{
    if (!keyboard_state_) {
        return;
    }

    LvglLock lvgl_lock;
    if (!lvgl_lock) {
        ESP_LOGW(SHELL_TAG, "Failed to lock LVGL while hiding keyboard");
        return;
    }

    std::lock_guard state_lock(keyboard_state_->mutex);
    if (keyboard_state_->app_id != app_id || keyboard_state_->request_id != request_id) {
        return;
    }
    if (keyboard_state_->overlay != nullptr && lv_obj_is_valid(keyboard_state_->overlay)) {
        lv_obj_delete(keyboard_state_->overlay);
    }
    keyboard_state_->app_id = esp_brookesia::system::core::INVALID_APP_ID;
    keyboard_state_->request_id =
        esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID;
    keyboard_state_->overlay = nullptr;
    keyboard_state_->text_area = nullptr;
    keyboard_state_->result_pending = false;
    keyboard_state_->confirmed = false;
    keyboard_state_->text.clear();
    ESP_LOGI(SHELL_TAG, "System keyboard closed");
}

void CircularShell::start_status()
{
    set_status_text(WATCH_FACE_TIME_PATH, "--:--");
    set_status_text(WATCH_FACE_DATE_PATH, "Waiting for sync");
    set_status_text(WIFI_PATH, "Wi-Fi: ?");
    set_status_text(BATTERY_PATH, "Bat: ?");

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
                    state->owner->set_status_text(WIFI_PATH, "Wi-Fi: linked");
                    state->owner->set_status_text(QUICK_WIFI_PATH, "Wi-Fi: linked (tap to stop)");
                } else if (event == "Deinited" || event == "Inited" || event == "Stopped" ||
                           event == "Started" || event == "Disconnected") {
                    state->owner->set_status_text(WIFI_PATH, "Wi-Fi: no link");
                    state->owner->set_status_text(QUICK_WIFI_PATH, "Wi-Fi: off/unlinked (tap)");
                } else {
                    state->owner->set_status_text(WIFI_PATH, "Wi-Fi: ?");
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
                    callback_state->owner->set_status_text(BATTERY_PATH, "Bat: ?");
                    callback_state->owner->set_status_text(BATTERY_CARD_PATH, "Battery: ?");
                    callback_state->owner->set_status_text(QUICK_BATTERY_PATH, "Battery: ?");
                    return;
                }
                DeviceHelper::PowerBatteryState state;
                if (!BROOKESIA_DESCRIBE_FROM_JSON(std::get<boost::json::object>(item->second), state) ||
                        !state.is_present || !state.percentage.has_value()) {
                    callback_state->owner->set_status_text(BATTERY_PATH, "Bat: ?");
                    callback_state->owner->set_status_text(BATTERY_CARD_PATH, "Battery: ?");
                    callback_state->owner->set_status_text(QUICK_BATTERY_PATH, "Battery: ?");
                    return;
                }
                const auto text = "Battery: " + std::to_string(*state.percentage) + "%";
                callback_state->owner->set_status_text(
                    BATTERY_PATH,
                    "Bat: " + std::to_string(*state.percentage) + "%"
                );
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
        set_status_text(WIFI_PATH, "Wi-Fi: ?");
        set_status_text(QUICK_WIFI_PATH, "Wi-Fi: ?");
        return;
    }
    auto state = WifiHelper::call_function_sync<std::string>(WifiHelper::FunctionId::GetGeneralState);
    if (!state) {
        set_status_text(WIFI_PATH, "Wi-Fi: ?");
        set_status_text(QUICK_WIFI_PATH, "Wi-Fi: ?");
    } else if (*state == "Connected") {
        set_status_text(WIFI_PATH, "Wi-Fi: linked");
        set_status_text(QUICK_WIFI_PATH, "Wi-Fi: linked (tap to stop)");
    } else if (*state == "Idle" || *state == "Initing" || *state == "Inited" || *state == "Deiniting" ||
               *state == "Starting" || *state == "Started" || *state == "Stopping" ||
               *state == "Connecting" || *state == "Disconnecting") {
        set_status_text(WIFI_PATH, "Wi-Fi: no link");
        set_status_text(QUICK_WIFI_PATH, "Wi-Fi: off/unlinked (tap)");
    } else {
        set_status_text(WIFI_PATH, "Wi-Fi: ?");
        set_status_text(QUICK_WIFI_PATH, "Wi-Fi: ?");
    }
}

void CircularShell::refresh_battery()
{
    if (!device_binding_.is_valid()) {
        set_status_text(BATTERY_PATH, "Bat: ?");
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
        set_status_text(BATTERY_PATH, "Bat: ?");
        set_status_text(BATTERY_CARD_PATH, "Battery: ?");
        set_status_text(QUICK_BATTERY_PATH, "Battery: ?");
        return;
    }
    set_status_text(BATTERY_PATH, "Bat: " + std::to_string(*state.percentage) + "%");
    const auto text = "Battery: " + std::to_string(*state.percentage) + "%";
    set_status_text(BATTERY_CARD_PATH, text);
    set_status_text(QUICK_BATTERY_PATH, text);
}

void CircularShell::refresh_brightness()
{
    auto value = DisplayHelper::call_function_sync<double>(
                     DisplayHelper::FunctionId::GetBacklightBrightness,
                     0.0
                 );
    const auto text = value ?
                      "Brightness: " + std::to_string(static_cast<int>(*value)) + "%" :
                      "Brightness: ?";
    set_status_text(BRIGHTNESS_CARD_PATH, text);
    set_status_text(QUICK_BRIGHTNESS_PATH, text);
}

std::expected<void, std::string> CircularShell::step_brightness()
{
    auto current = DisplayHelper::call_function_sync<double>(
                       DisplayHelper::FunctionId::GetBacklightBrightness,
                       0.0
                   );
    if (!current) {
        return std::unexpected("Failed to read brightness: " + current.error());
    }
    const double next = *current >= 100.0 ? 20.0 : std::min(100.0, *current + 20.0);
    auto result = DisplayHelper::call_function_sync<void>(
                      DisplayHelper::FunctionId::SetBacklightBrightness,
                      0.0,
                      next
                  );
    if (!result) {
        return std::unexpected("Failed to set brightness: " + result.error());
    }
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
