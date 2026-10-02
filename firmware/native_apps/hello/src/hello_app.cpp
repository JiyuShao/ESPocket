#include "espocket/hello_app.hpp"

#include <string>

#include "esp_log.h"
#include "espocket/page_navigator.hpp"

namespace espocket {
extern const char hello_gui_json_start[] asm("_binary_hello_gui_json_start");
namespace {

constexpr char TAG[] = "ESPocket.Hello";
constexpr std::string_view INCREMENT_ACTION = "hello.increment";
constexpr std::string_view OPEN_DETAIL_ACTION = "hello.open_detail";
constexpr std::string_view TOGGLE_CONFIRM_ACTION = "hello.toggle_confirm";
constexpr std::string_view ALLOW_BACK_ACTION = "hello.allow_back";
constexpr std::string_view CANCEL_BACK_ACTION = "hello.cancel_back";
constexpr std::string_view BACK_STATUS_TIMER = "hello.back_status";
constexpr std::string_view BACK_STATUS_PATH = "/detail/hint";
constexpr std::string_view CONFIRM_LABEL_PATH = "/detail/confirm/label";
constexpr std::string_view MAIN_FLOW = "main";
constexpr std::string_view OPEN_DETAIL_TRANSITION = "open_detail";
constexpr std::string_view BACK_ROOT_TRANSITION = "back_root";
constexpr std::string_view COUNTER_PATH = "/root/counter";

} // namespace

PageDeclaration HelloApp::get_page_declaration() const
{
    return {
        .app_id = "espocket.app.hello",
        .root_page_id = "root",
        .page_ids = {"root", "detail"},
        .cards = {{"summary", "root"}, {"detail", "detail"}},
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
    // A late callback from a stopped instance cannot overwrite this instance's token.
    back_confirmation_ = std::make_shared<BackConfirmation>();
    back_status_.clear();

    for (const auto action : {INCREMENT_ACTION, OPEN_DETAIL_ACTION, TOGGLE_CONFIRM_ACTION,
                             ALLOW_BACK_ACTION, CANCEL_BACK_ACTION}) {
        auto action_result = context.gui().subscribe_action(action);
        if (!action_result) {
            return std::unexpected("Failed to subscribe action: " + action_result.error());
        }
    }

    auto text_result = context.gui().set_text(COUNTER_PATH, "Counter: 0");
    if (!text_result) {
        return std::unexpected("Failed to reset counter text: " + text_result.error());
    }

    auto timer = context.timer().start_periodic(BACK_STATUS_TIMER, 100);
    if (!timer) {
        return std::unexpected("Failed to start Back status timer: " + timer.error());
    }
    back_status_timer_ = *timer;
    context_ = &context;
    if (auto navigator = navigator_.lock()) {
        navigator->set_back_handler([state = back_confirmation_](const PageSnapshot &, uint64_t token) {
            if (!state->enabled.load()) return BackDecision::Allow;
            state->pending_token.store(token);
            return BackDecision::Defer;
        });
    }
    ESP_LOGI(TAG, "Hello Native started");
    return {};
}

std::expected<void, std::string> HelloApp::on_stop(
    esp_brookesia::system::core::AppContext &context
)
{
    context.timer().stop(back_status_timer_);
    back_status_timer_ = 0;
    if (auto navigator = navigator_.lock()) navigator->set_back_handler({});
    back_confirmation_->pending_token.store(0);
    back_confirmation_->enabled.store(false);
    back_status_.clear();
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
        auto label = context.gui().set_text(CONFIRM_LABEL_PATH,
            back_confirmation_->enabled.load() ? "Back confirm: On" : "Back confirm: Off");
        if (!label) return std::unexpected(label.error());
        back_status_.clear();
        return {};
    }
    if (action == TOGGLE_CONFIRM_ACTION) {
        if (back_confirmation_->pending_token.load() != 0) return std::unexpected("Back confirmation is pending");
        const bool enabled = !back_confirmation_->enabled.load();
        auto result = context.gui().set_text(CONFIRM_LABEL_PATH,
            enabled ? "Back confirm: On" : "Back confirm: Off");
        if (!result) return std::unexpected(result.error());
        back_confirmation_->enabled.store(enabled);
        back_status_.clear();
        return {};
    }
    if (action == ALLOW_BACK_ACTION || action == CANCEL_BACK_ACTION) {
        auto navigator = navigator_.lock();
        if (!navigator) return std::unexpected("App Navigator is unavailable");
        const auto token = back_confirmation_->pending_token.exchange(0);
        if (token == 0) return std::unexpected("No Back confirmation is pending");
        auto result = navigator->complete_back(token, action == ALLOW_BACK_ACTION);
        back_status_.clear();
        if (!result) return std::unexpected("Back confirmation failed: " + std::to_string(static_cast<int>(result.error())));
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

std::expected<void, std::string> HelloApp::on_timer(
    esp_brookesia::system::core::AppContext &context,
    esp_brookesia::system::core::TimerId timer_id,
    std::string_view name
)
{
    if (timer_id != back_status_timer_ || name != BACK_STATUS_TIMER) return {};
    auto navigator = navigator_.lock();
    if (!navigator) return {};
    auto observed_token = back_confirmation_->pending_token.load();
    const auto snapshot = navigator->snapshot();
    if (snapshot.page_id != "detail") return {};
    std::string status;
    if (snapshot.back_pending) {
        status = "Back? Allow or Cancel";
    } else if (observed_token != 0 &&
               back_confirmation_->pending_token.compare_exchange_strong(observed_token, 0)) {
        status = "Back expired or invalidated";
    } else if (back_status_ == "Back expired or invalidated") {
        status = back_status_; // Keep the error readable until an action or a new request.
    } else {
        status = back_confirmation_->enabled.load() ? "Use Back to confirm" : "Edge Back returns to Root";
    }
    if (status == back_status_) return {};
    auto result = context.gui().set_text(BACK_STATUS_PATH, status);
    if (!result) return std::unexpected(result.error());
    back_status_ = std::move(status);
    return {};
}

} // namespace espocket
