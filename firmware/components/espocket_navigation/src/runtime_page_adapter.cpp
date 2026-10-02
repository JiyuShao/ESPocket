#include "espocket/runtime_page_adapter.hpp"

#include <algorithm>
#include <charconv>
#include "boost/json.hpp"

namespace espocket {

std::expected<std::shared_ptr<RuntimePageAdapter>, std::string> RuntimePageAdapter::create(
    RuntimePageDefinition definition, FlowPresenter presenter)
{
    if (!presenter || !validate_runtime_pages(definition)) return std::unexpected("invalid_declaration");
    const auto root = definition.declaration.root_page_id;
    auto navigator = PageNavigator::create(std::move(definition.declaration),
        [root, flow = std::move(definition.screen_flow), transitions = std::move(definition.transitions),
         presenter = std::move(presenter)](std::string_view from, std::string_view to) {
            if (from.empty()) return to == root; // Core mounts the declared initial Root.
            if (from == to) return true;
            const auto found = std::ranges::find_if(transitions, [&](const auto &transition) {
                return transition.from == from && transition.to == to;
            });
            return found != transitions.end() && presenter(flow, found->action, from, to);
        });
    if (!navigator) return std::unexpected(std::string(navigation_error_name(navigator.error())));
    return std::shared_ptr<RuntimePageAdapter>(new RuntimePageAdapter(
        std::make_shared<PageNavigator>(std::move(*navigator))));
}

std::expected<void, NavigationError> RuntimePageAdapter::start()
{
    if (!navigator_->snapshot().page_id.empty()) return std::unexpected(NavigationError::InvalidDeclaration);
    back_ = std::make_shared<BackState>();
    navigator_->set_back_handler([state = back_](const PageSnapshot &, uint64_t token) {
        const auto decision = state->decision.load();
        if (decision == BackDecision::Defer) state->token.store(token);
        return decision;
    });
    return navigator_->start();
}

void RuntimePageAdapter::stop()
{
    navigator_->stop();
    navigator_->set_back_handler({});
    back_.reset();
}

std::expected<std::string, std::string> RuntimePageAdapter::dispatch(std::string_view request_json, uint64_t now_ms)
{
    if (request_json.size() > 4096) return std::unexpected("bad_request");
    boost::system::error_code parse_error;
    auto request = boost::json::parse(request_json, parse_error);
    if (parse_error || !request.is_object()) return std::unexpected("bad_request");
    const auto &object = request.as_object();
    const auto *operation = object.if_contains("operation");
    if (!operation || !operation->is_string()) return std::unexpected("bad_request");
    const auto name = operation->as_string();
    // Each operation accepts exactly its own fields; parameters are never silently dropped.
    auto fields = [&](std::initializer_list<std::string_view> allowed) {
        return std::ranges::all_of(object, [&](const auto &entry) {
            return std::ranges::find(allowed, std::string_view(entry.key())) != allowed.end();
        });
    };
    if (!back_ || navigator_->snapshot().page_id.empty()) return std::unexpected("not_started");
    std::expected<void, NavigationError> result;
    if (name == "push" || name == "replace") {
        const auto *page = object.if_contains("pageId");
        if (!fields({"operation", "pageId"}) || !page || !page->is_string()) return std::unexpected("bad_request");
        result = name == "push" ? navigator_->push(std::string_view(page->as_string())) :
                                  navigator_->replace(std::string_view(page->as_string()));
    } else if (name == "completeBack") {
        const auto *token = object.if_contains("token");
        const auto *allow = object.if_contains("allow");
        if (!fields({"operation", "token", "allow"}) || !token || !token->is_string() ||
            !allow || !allow->is_bool()) return std::unexpected("bad_request");
        const std::string_view number(token->as_string());
        uint64_t parsed_token = 0;
        auto parsed = std::from_chars(number.data(), number.data() + number.size(), parsed_token);
        if (parsed.ec != std::errc{} || parsed.ptr != number.data() + number.size() || parsed_token == 0) {
            return std::unexpected("bad_request");
        }
        result = navigator_->complete_back(parsed_token, allow->as_bool());
        if (result) back_->token.store(0);
    } else if (name == "setBackDecision") {
        const auto *decision = object.if_contains("decision");
        if (!fields({"operation", "decision"}) || !decision || !decision->is_string()) return std::unexpected("bad_request");
        if (navigator_->snapshot().back_pending) return std::unexpected("back_pending");
        if (decision->as_string() == "allow") back_->decision.store(BackDecision::Allow);
        else if (decision->as_string() == "cancel") back_->decision.store(BackDecision::Cancel);
        else if (decision->as_string() == "defer") back_->decision.store(BackDecision::Defer);
        else return std::unexpected("bad_request");
    } else {
        if (!fields({"operation"})) return std::unexpected("bad_request");
        if (name == "pop") result = navigator_->pop();
        else if (name == "resetToRoot") result = navigator_->reset_to_root();
        else if (name == "requestBack") {
            auto back = navigator_->request_back(now_ms);
            if (!back) result = std::unexpected(back.error());
        } else if (name != "snapshot") return std::unexpected("unsupported");
    }
    if (!result) return std::unexpected(std::string(navigation_error_name(result.error())));
    const auto snapshot = navigator_->snapshot();
    auto value = boost::json::parse(encode_page_snapshot(snapshot)).as_object();
    // App-private confirmation token uses a string to preserve all uint64 bits in JS.
    value["pendingToken"] = snapshot.back_pending ? boost::json::value(std::to_string(back_->token.load())) : boost::json::value(nullptr);
    return boost::json::serialize(value);
}

} // namespace espocket
