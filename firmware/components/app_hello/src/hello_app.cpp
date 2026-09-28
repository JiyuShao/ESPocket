#include "espocket/hello_app.hpp"

#include <string>

#include "esp_log.h"

namespace espocket {
namespace {

constexpr char TAG[] = "ESPocket.Hello";
constexpr std::string_view INCREMENT_ACTION = "hello.increment";
constexpr std::string_view COUNTER_PATH = "/root/counter";
constexpr std::string_view HELLO_JSON = R"json({
  "version": "0.1.0",
  "assets": [
    {
      "type": "viewScreen",
      "id": "root",
      "commonProps": { "scrollable": false },
      "style": { "bgColor": "#101722", "padding": 0 },
      "layout": {
        "type": "flex",
        "flexFlow": "column",
        "mainAlign": "center",
        "crossAlign": "center",
        "gap": "20dp"
      },
      "children": [
        {
          "type": "label",
          "id": "title",
          "labelProps": { "text": "Hello ESPocket" },
          "style": { "textColor": "#f4f7fb", "fontSize": "32sp", "textAlign": "center" },
          "placement": { "width": "300dp", "height": "44dp" }
        },
        {
          "type": "label",
          "id": "counter",
          "labelProps": { "text": "Counter: 0" },
          "style": { "textColor": "#cbd5e1", "fontSize": "20sp", "textAlign": "center" },
          "placement": { "width": "220dp", "height": "30dp" }
        },
        {
          "type": "button",
          "id": "increment",
          "events": [ { "type": "clicked", "action": "hello.increment" } ],
          "style": { "bgColor": "#2157d5", "radius": "28dp" },
          "placement": { "width": "210dp", "height": "74dp" },
          "children": [
            {
              "type": "label",
              "id": "label",
              "labelProps": { "text": "Increment" },
              "style": { "textColor": "#ffffff", "fontSize": "20sp" },
              "placement": { "mode": "relative", "align": "center" }
            }
          ]
        },
        {
          "type": "button",
          "id": "detail",
          "events": [ { "type": "clicked", "action": "open_detail" } ],
          "style": { "bgColor": "#334155", "radius": "24dp" },
          "placement": { "width": "190dp", "height": "54dp" },
          "children": [
            {
              "type": "label",
              "id": "label",
              "labelProps": { "text": "Open Detail" },
              "style": { "textColor": "#ffffff", "fontSize": "18sp" },
              "placement": { "mode": "relative", "align": "center" }
            }
          ]
        }
      ]
    },
    {
      "type": "viewScreen",
      "id": "detail",
      "commonProps": { "scrollable": false },
      "style": { "bgColor": "#172033", "padding": 0 },
      "layout": { "type": "flex", "flexFlow": "column", "mainAlign": "center", "crossAlign": "center", "gap": "18dp" },
      "children": [
        { "type": "label", "id": "title", "labelProps": { "text": "Native Detail" }, "style": { "textColor": "#ffffff", "fontSize": "30sp" }, "placement": { "width": "280dp", "height": "44dp" } },
        { "type": "label", "id": "hint", "labelProps": { "text": "Edge Back returns to Root" }, "style": { "textColor": "#a8b3c5", "fontSize": "17sp", "textAlign": "center" }, "placement": { "width": "300dp", "height": "30dp" } }
      ]
    },
    {
      "type": "screenFlow",
      "id": "main",
      "screens": [ "root", "detail" ],
      "initial": "root",
      "transitions": [
        { "from": ["root"], "action": "open_detail", "to": "detail" },
        { "from": ["detail"], "action": "back_root", "to": "root" }
      ]
    }
  ]
})json";

} // namespace

esp_brookesia::system::core::AppManifest HelloApp::get_manifest() const
{
    esp_brookesia::system::core::AppManifest manifest{};
    manifest.id = "espocket.app.hello";
    manifest.name = "Hello Native";
    manifest.localized_names = {
        {"en", "Hello Native"},
        {"zh_CN", "你好 Native"},
    };
    manifest.version = "0.1.0";
    manifest.kind = esp_brookesia::system::core::AppKind::Native;
    manifest.visible = true;
    return manifest;
}

esp_brookesia::system::core::AppGuiDescriptor HelloApp::get_gui_descriptor() const
{
    return {
        .root_kind = esp_brookesia::system::core::GuiRootKind::JsonString,
        .root = std::string(HELLO_JSON),
        .resources = {},
        .screen_flows = {
            {
                .screen_flow = "main",
                .layer = esp_brookesia::system::core::GuiAppLayer::AppDefault,
            },
        },
    };
}

std::expected<void, std::string> HelloApp::on_start(
    esp_brookesia::system::core::AppContext &context
)
{
    count_ = 0;

    auto action_result = context.gui().subscribe_action(INCREMENT_ACTION);
    if (!action_result) {
        return std::unexpected("Failed to subscribe increment action: " + action_result.error());
    }

    auto text_result = context.gui().set_text(COUNTER_PATH, "Counter: 0");
    if (!text_result) {
        return std::unexpected("Failed to reset counter text: " + text_result.error());
    }

    ESP_LOGI(TAG, "Hello Native started");
    return {};
}

std::expected<void, std::string> HelloApp::on_stop(
    esp_brookesia::system::core::AppContext &context
)
{
    (void)context;
    count_ = 0;
    ESP_LOGI(TAG, "Hello Native stopped");
    return {};
}

std::expected<void, std::string> HelloApp::on_action(
    esp_brookesia::system::core::AppContext &context,
    std::string_view action
)
{
    if (action != INCREMENT_ACTION) {
        return {};
    }

    const auto next_count = count_ + 1;
    auto result = context.gui().set_text(COUNTER_PATH, "Counter: " + std::to_string(next_count));
    if (!result) {
        return std::unexpected("Failed to update counter text: " + result.error());
    }
    count_ = next_count;
    return {};
}

} // namespace espocket
