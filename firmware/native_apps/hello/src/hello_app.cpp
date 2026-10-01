#include "espocket/hello_app.hpp"

#include <string>

#include "esp_log.h"
#include "espocket/page_navigator.hpp"

namespace espocket {
namespace {

constexpr char TAG[] = "ESPocket.Hello";
constexpr std::string_view INCREMENT_ACTION = "hello.increment";
constexpr std::string_view OPEN_DETAIL_ACTION = "hello.open_detail";
constexpr std::string_view MAIN_FLOW = "main";
constexpr std::string_view OPEN_DETAIL_TRANSITION = "open_detail";
constexpr std::string_view BACK_ROOT_TRANSITION = "back_root";
constexpr std::string_view COUNTER_PATH = "/root/counter";
extern const char hello_gui_json_start[] asm("_binary_hello_gui_json_start");

} // namespace

PageDeclaration HelloApp::get_page_declaration() const
{
    return {
        .app_id = "espocket.app.hello",
        .root_page_id = "root",
        .page_ids = {"root", "detail"},
        .cards = {},
    };
}

void HelloApp::set_navigator(std::weak_ptr<PageNavigator> navigator)
{
    navigator_ = std::move(navigator);
}

bool HelloApp::present_page(std::string_view from, std::string_view to)
{
    if (context_ == nullptr) {
        return false;
    }
    if (from.empty() && to == "root") {
        return true; // Brookesia loads the flow at its declared initial screen.
    }
    const auto transition = from == "root" && to == "detail"
                                ? OPEN_DETAIL_TRANSITION
                                : from == "detail" && to == "root"
                                      ? BACK_ROOT_TRANSITION
                                      : std::string_view{};
    if (transition.empty()) {
        return false;
    }
    auto result = context_->gui().trigger_screen_flow(MAIN_FLOW, transition);
    if (!result) {
        ESP_LOGW(TAG, "Page presentation failed: %s", result.error().c_str());
    }
    return result.has_value();
}

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
        .root = std::string(hello_gui_json_start),
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
    action_result = context.gui().subscribe_action(OPEN_DETAIL_ACTION);
    if (!action_result) {
        return std::unexpected("Failed to subscribe Detail action: " + action_result.error());
    }

    auto text_result = context.gui().set_text(COUNTER_PATH, "Counter: 0");
    if (!text_result) {
        return std::unexpected("Failed to reset counter text: " + text_result.error());
    }

    context_ = &context;
    ESP_LOGI(TAG, "Hello Native started");
    return {};
}

std::expected<void, std::string> HelloApp::on_stop(
    esp_brookesia::system::core::AppContext &context
)
{
    (void)context;
    context_ = nullptr;
    count_ = 0;
    ESP_LOGI(TAG, "Hello Native stopped");
    return {};
}

std::expected<void, std::string> HelloApp::on_action(
    esp_brookesia::system::core::AppContext &context,
    std::string_view action
)
{
    if (action == OPEN_DETAIL_ACTION) {
        auto navigator = navigator_.lock();
        if (!navigator) {
            return std::unexpected("App Navigator is unavailable");
        }
        auto result = navigator->push("detail");
        if (!result) {
            return std::unexpected("Failed to navigate to Detail");
        }
        return {};
    }
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
