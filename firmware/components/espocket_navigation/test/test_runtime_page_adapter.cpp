#include "espocket/runtime_page_adapter.hpp"
#include "espocket/navigation_request_queue.hpp"
#include "boost/json.hpp"
#include <cassert>

using namespace espocket;
constexpr auto declaration = R"({"version":1,"appId":"app","rootPageId":"root","pageIds":["root","detail"],"cards":[{"cardId":"summary","targetPageId":"detail"}],"presentation":{"screenFlow":"main","transitions":[{"from":"root","to":"detail","action":"open"},{"from":"detail","to":"root","action":"back"}]}})";

int main()
{
    NavigationRequestQueue queue;
    int executions = 0;
    std::string reply;
    auto receive = [&](NavigationRequestQueue::Result result) { reply = result ? *result : result.error(); };
    auto execute = [&](uint32_t app, std::string_view json) -> NavigationRequestQueue::Result {
        assert(app == 1 && json == "request"); ++executions; return "done";
    };
    queue.enqueue(1, 0, 0, "request", receive); assert(reply == "not_started");
    queue.enqueue(1, 7, 0, "request", receive); assert(executions == 0);
    queue.drain(1, 7, 1999, execute); assert(reply == "done" && executions == 1);
    queue.enqueue(1, 7, 0, "request", receive);
    queue.drain(1, 7, 2000, execute); assert(reply == "timeout" && executions == 1);
    queue.enqueue(1, 7, 0, "request", receive);
    queue.drain(1, 8, 10, execute); assert(reply == "stale_request" && executions == 1);
    for (size_t i = 0; i < NavigationRequestQueue::CAPACITY; ++i) queue.enqueue(1, 8, 0, "request", receive);
    queue.enqueue(1, 8, 0, "request", receive); assert(reply == "busy");
    queue.close(); assert(reply == "system_unavailable" && executions == 1);
    queue.enqueue(1, 8, 0, "request", receive); assert(reply == "system_unavailable");
    auto parsed = decode_runtime_pages(declaration);
    assert(parsed && parsed->declaration.app_id == "app");
    bool peer_presentation = true;
    auto native = PageNavigator::create(parsed->declaration, [&](auto from, auto) { return from.empty() || peer_presentation; });
    auto runtime = RuntimePageAdapter::create(*parsed, [&](auto, auto, auto, auto) { return peer_presentation; });
    assert(native && runtime && native->start() && (*runtime)->start());
    auto compare = [&](std::string_view command, std::expected<void, NavigationError> native_result) {
        const auto runtime_result = (*runtime)->dispatch(command, 0);
        assert(bool(runtime_result) == bool(native_result));
        if (!native_result) assert(runtime_result.error() == navigation_error_name(native_result.error()));
        const auto a = native->snapshot(), b = (*runtime)->navigator()->snapshot();
        assert(a.app_id == b.app_id && a.page_id == b.page_id && a.can_back == b.can_back && a.back_pending == b.back_pending);
    };
    compare(R"({"operation":"pop"})", native->pop());
    compare(R"({"operation":"push","pageId":"missing"})", native->push("missing"));
    compare(R"({"operation":"push","pageId":"detail"})", native->push("detail"));
    compare(R"({"operation":"replace","pageId":"detail"})", native->replace("detail"));
    compare(R"({"operation":"resetToRoot"})", native->reset_to_root());
    compare(R"({"operation":"push","pageId":"detail"})", native->push("detail"));
    native->set_back_handler([](const auto &, uint64_t) { return BackDecision::Defer; });
    assert((*runtime)->dispatch(R"({"operation":"setBackDecision","decision":"defer"})", 0));
    auto native_back = native->request_back(0);
    assert(native_back && native_back->has_value());
    compare(R"({"operation":"requestBack"})", {});
    auto repeated = native->request_back(0);
    compare(R"({"operation":"requestBack"})", std::unexpected(repeated.error()));
    auto peer_token = boost::json::parse(*(*runtime)->dispatch(R"({"operation":"snapshot"})", 0)).as_object()["pendingToken"];
    assert(native->expire_back(15'000) == (*runtime)->navigator()->expire_back(15'000));
    auto peer_complete = boost::json::serialize(boost::json::object{{"operation", "completeBack"}, {"token", peer_token}, {"allow", true}});
    compare(peer_complete, native->complete_back(native_back->value(), true));
    native->stop(); (*runtime)->stop();
    assert(native->start() && (*runtime)->start());
    compare(peer_complete, native->complete_back(native_back->value(), true));
    compare(R"({"operation":"push","pageId":"detail"})", native->push("detail"));
    peer_presentation = false;
    compare(R"({"operation":"pop"})", native->pop());
    peer_presentation = true;
    auto invalid_typed = *parsed;
    invalid_typed.transitions.front().to = "missing";
    assert(!RuntimePageAdapter::create(invalid_typed, [](auto, auto, auto, auto) { return true; }));
    for (const auto &bad : {"{}", "[]", "null", "not-json"}) assert(!decode_runtime_pages(bad));
    auto value = boost::json::parse(declaration).as_object();
    auto check_bad = [&](const auto &changed) { assert(!decode_runtime_pages(boost::json::serialize(changed))); };
    value["version"] = 2;
    assert(decode_runtime_pages(boost::json::serialize(value)).error() == "unsupported_version");
    value["version"] = 1;
    value["pageIds"] = boost::json::array{"detail"}; check_bad(value);
    value["pageIds"] = boost::json::array{"root", "root"}; check_bad(value);
    value["pageIds"] = boost::json::array{"root", "detail"};
    value["usesStandardBackControl"] = 1; check_bad(value); value.erase("usesStandardBackControl");
    value["backPresentation"] = "unknown"; check_bad(value); value.erase("backPresentation");
    value["cards"].as_array().front().as_object()["targetPageId"] = 3; check_bad(value);
    value["cards"].as_array().front().as_object()["targetPageId"] = "unknown"; check_bad(value);
    value["cards"].as_array().front().as_object()["targetPageId"] = "detail";
    value["presentation"].as_object()["transitions"].as_array().push_back(
        value["presentation"].as_object()["transitions"].as_array().front()); check_bad(value);
    bool presentation_ok = true;
    auto adapter = RuntimePageAdapter::create(*parsed, [&](auto flow, auto action, auto from, auto to) {
        assert(flow == "main" && (action == "open" || action == "back"));
        assert(from != to);
        return presentation_ok;
    });
    assert(adapter);
    auto dispatch = [&](std::string_view command) { return (*adapter)->dispatch(command, 100); };
    assert(dispatch(R"({"operation":"snapshot"})").error() == "not_started");
    assert((*adapter)->start());
    assert(dispatch(R"({"operation":"pop"})").error() == "at_root");
    assert(dispatch(R"({"operation":"push","pageId":"missing"})").error() == "unknown_page");
    assert(dispatch(R"({"operation":"push","pageId":"root"})").error() == "root_page");
    assert(dispatch(R"({"operation":"push","pageId":"detail","parameters":{"secret":1}})").error() == "bad_request");
    assert(dispatch(R"({"operation":"push","pageId":"detail"})"));
    assert(dispatch(R"({"operation":"setBackDecision","decision":"defer"})"));
    assert((*adapter)->start().error() == NavigationError::InvalidDeclaration);
    auto pending = dispatch(R"({"operation":"requestBack"})");
    assert(pending);
    auto state = boost::json::parse(*pending).as_object();
    assert(state["backPending"].as_bool() && !state["canBack"].as_bool());
    auto token = std::string(state["pendingToken"].as_string());
    assert(dispatch(R"({"operation":"requestBack"})").error() == "back_pending");
    assert(dispatch(R"({"operation":"setBackDecision","decision":"allow"})").error() == "back_pending");
    auto complete = [&](bool allow) {
        return dispatch(boost::json::serialize(boost::json::object{
            {"operation", "completeBack"}, {"token", token}, {"allow", allow}}));
    };
    assert(complete(false));
    assert((*adapter)->navigator()->snapshot().page_id == "detail");
    assert(complete(true).error() == "stale_request");
    pending = dispatch(R"({"operation":"requestBack"})");
    token = std::string(boost::json::parse(*pending).as_object()["pendingToken"].as_string());
    assert((*adapter)->navigator()->expire_back(15'099) == std::nullopt);
    assert((*adapter)->navigator()->expire_back(15'100) == NavigationError::BackTimeout);
    assert(complete(true).error() == "stale_request");
    assert(dispatch(R"({"operation":"setBackDecision","decision":"cancel"})"));
    assert(dispatch(R"({"operation":"requestBack"})").error() == "back_cancelled");
    assert(dispatch(R"({"operation":"setBackDecision","decision":"allow"})"));
    presentation_ok = false;
    assert(dispatch(R"({"operation":"requestBack"})").error() == "presentation_failed");
    assert((*adapter)->navigator()->snapshot().can_back);
    presentation_ok = true;
    assert(dispatch(R"({"operation":"replace","pageId":"detail"})"));
    assert(dispatch(R"({"operation":"resetToRoot"})"));
    assert(!(*adapter)->navigator()->snapshot().can_back);
    assert(dispatch(R"({"operation":"push","pageId":"detail"})"));
    assert(dispatch(R"({"operation":"setBackDecision","decision":"defer"})"));
    pending = dispatch(R"({"operation":"requestBack"})");
    token = std::string(boost::json::parse(*pending).as_object()["pendingToken"].as_string());
    (*adapter)->stop();
    assert((*adapter)->start());
    assert(complete(true).error() == "stale_request");
    assert(dispatch(R"({"operation":"push","pageId":"detail"})"));
    assert(dispatch(R"({"operation":"requestBack"})")); // New running instance defaults to Allow.
    assert((*adapter)->navigator()->snapshot().page_id == "root");
    assert(!(*adapter)->navigator()->edge_back_enabled());
}
