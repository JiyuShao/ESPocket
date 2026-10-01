#include <cstdlib>
#include <cstdint>
#include <chrono>
#include <future>
#include <iostream>
#include <string_view>

#include "espocket/page_navigator.hpp"

using espocket::NavigationError;
using espocket::BackDecision;
using espocket::BackPresentation;
using espocket::PageDeclaration;
using espocket::PageNavigator;

void require(bool condition, std::string_view message)
{
    if (!condition) {
        std::cerr << message << '\n';
        std::exit(1);
    }
}

int main()
{
    auto created = PageNavigator::create(
        PageDeclaration{
            .app_id = "espocket.app.hello",
            .root_page_id = "root",
            .page_ids = {"root", "detail"},
        },
        [](std::string_view, std::string_view) { return true; }
    );
    require(created.has_value(), "valid declaration should install");
    auto navigator = std::move(*created);

    require(navigator.start().has_value(), "start should show Root");
    require(navigator.snapshot().page_id == "root", "Root should be current after start");
    require(navigator.snapshot().app_id == "espocket.app.hello" &&
                !navigator.snapshot().back_pending,
            "snapshot should expose stable App and Back semantics");
    require(!navigator.snapshot().can_back, "Root must not offer Back");
    auto duplicate_root = navigator.push("root");
    require(!duplicate_root && duplicate_root.error() == NavigationError::RootPage,
            "Root must remain the unique bottom Page");
    require(navigator.snapshot().page_id == "root", "rejected Root push must preserve state");

    require(navigator.push("detail").has_value(), "declared Detail should open");
    require(navigator.snapshot().page_id == "detail", "Detail should be current after push");
    require(navigator.snapshot().can_back, "Detail should offer Back");
    auto unknown = navigator.replace("missing");
    require(!unknown && unknown.error() == NavigationError::UnknownPage &&
                navigator.snapshot().page_id == "detail",
            "unknown replacement must leave the current Page intact");
    require(navigator.replace("detail").has_value(), "declared child replacement should succeed");
    require(navigator.reset_to_root().has_value() &&
                navigator.snapshot().page_id == "root" && !navigator.snapshot().can_back,
            "reset should clear every child Page");
    require(navigator.push("detail").has_value(), "Detail should reopen after reset");

    require(navigator.pop().has_value(), "Back should return to Root");
    require(navigator.snapshot().page_id == "root", "Root should be current after Back");
    require(!navigator.snapshot().can_back, "Root must still have no Back");
    auto root_back = navigator.pop();
    require(!root_back && root_back.error() == NavigationError::AtRoot,
            "Back at Root must fail without leaving App");

    navigator.stop();
    auto missing_card = navigator.start_from_card("removed-card");
    require(!missing_card && missing_card.error() == NavigationError::TargetUnavailable,
            "removed Card target should report a diagnostic error");
    require(navigator.snapshot().page_id == "root" && !navigator.snapshot().can_back,
            "removed Card target must fall back to Root");

    navigator.stop();
    require(navigator.snapshot().page_id.empty(), "stopped task must not expose a stale Page");
    require(navigator.start().has_value(), "new task should start again");
    require(navigator.snapshot().page_id == "root" && !navigator.snapshot().can_back,
            "new task must start at Root");

    auto invalid = PageNavigator::create(
        PageDeclaration{
            .app_id = "espocket.app.hello",
            .root_page_id = "root",
            .page_ids = {"root", "detail", "detail"},
        },
        [](std::string_view, std::string_view) { return true; }
    );
    require(!invalid && invalid.error() == NavigationError::InvalidDeclaration,
            "duplicate Page IDs must fail installation");

    auto bad_card = PageNavigator::create(
        PageDeclaration{
            .app_id = "espocket.app.hello",
            .root_page_id = "root",
            .page_ids = {"root", "detail"},
            .cards = {{"shortcut", "removed-detail"}},
        },
        [](std::string_view, std::string_view) { return true; }
    );
    require(!bad_card && bad_card.error() == NavigationError::InvalidDeclaration,
            "Card target must reference a declared Page");

    auto failed_presentation = PageNavigator::create(
        PageDeclaration{
            .app_id = "espocket.app.hello",
            .root_page_id = "root",
            .page_ids = {"root", "detail"},
        },
        [](std::string_view, std::string_view to) { return to == "root"; }
    );
    require(failed_presentation.has_value(), "presenter failure is a runtime event");
    require(failed_presentation->start().has_value(), "Root should open before failed Detail");
    auto failed_push = failed_presentation->push("detail");
    require(!failed_push && failed_push.error() == NavigationError::PresentationFailed,
            "failed visual transition must not report success");
    require(failed_presentation->snapshot().page_id == "root",
            "failed visual transition must preserve the stack");

    auto card = PageNavigator::create(
        PageDeclaration{
            .app_id = "espocket.app.hello",
            .root_page_id = "root",
            .page_ids = {"root", "detail"},
            .cards = {{"native-card", "detail"}},
        },
        [](std::string_view, std::string_view) { return true; }
    );
    require(card.has_value(), "declared Card target should install");
    require(card->start_from_card("native-card").has_value(),
            "Card should open its target above Root");
    require(card->snapshot().page_id == "detail" && card->snapshot().can_back,
            "Card target should expose child Page Back");
    require(card->pop().has_value() && card->snapshot().page_id == "root",
            "Card target Back should return to App Root");

    auto back = PageNavigator::create(
        PageDeclaration{
            .app_id = "espocket.app.hello",
            .root_page_id = "root",
            .page_ids = {"root", "detail"},
        },
        [](std::string_view, std::string_view) { return true; }
    );
    require(back && back->start() && back->push("detail"), "Back fixture should open Detail");
    auto immediate = back->request_back(100);
    require(immediate && !immediate->has_value() && back->snapshot().page_id == "root",
            "default Back should pop once without a pending token");
    auto at_root = back->request_back(101);
    require(!at_root && at_root.error() == NavigationError::AtRoot,
            "Root should not accept a Back request");

    require(back->push("detail").has_value(), "Detail should reopen for deferred Back");
    back->set_back_handler([](const auto &, uint64_t) { return BackDecision::Defer; });
    auto deferred = back->request_back(200);
    require(deferred && deferred->has_value(), "deferred Back should provide a token");
    const auto token = deferred->value();
    require(back->snapshot().back_pending && !back->snapshot().can_back,
            "pending Back should disable repeated Back in the snapshot");
    auto duplicate = back->request_back(201);
    require(!duplicate && duplicate.error() == NavigationError::BackPending,
            "pending Back must reject duplicate requests");
    require(back->complete_back(token, false).has_value(), "App should be able to cancel Back");
    require(back->snapshot().page_id == "detail" && !back->snapshot().back_pending,
            "cancel should preserve Detail and clear pending state");
    auto stale = back->complete_back(token, true);
    require(!stale && stale.error() == NavigationError::StaleRequest,
            "completed token must not be reusable");

    auto deferred_again = back->request_back(300);
    require(deferred_again && deferred_again->has_value(), "second Back should get a new token");
    const auto second_token = deferred_again->value();
    require(second_token != token, "Back tokens must be unique within a task");
    require(!back->expire_back(300 + PageNavigator::BACK_TIMEOUT_MS - 1),
            "Back should remain pending until timeout");
    require(back->expire_back(300 + PageNavigator::BACK_TIMEOUT_MS) ==
                NavigationError::BackTimeout,
            "expired Back should report its timeout");
    require(back->snapshot().page_id == "detail" && !back->snapshot().back_pending,
            "timeout must preserve the current Page");
    auto late = back->complete_back(second_token, true);
    require(!late && late.error() == NavigationError::StaleRequest,
            "late approval must not navigate");

    auto pending_before_stop = back->request_back(1000);
    require(pending_before_stop && pending_before_stop->has_value(),
            "Back should be deferrable before PWR Home");
    const auto old_task_token = pending_before_stop->value();
    back->stop();
    require(back->start().has_value() && back->push("detail").has_value(),
            "new task should start cleanly");
    auto pending_new_task = back->request_back(1100);
    require(pending_new_task && pending_new_task->has_value(),
            "new task should accept a new deferred Back");
    require(!back->complete_back(old_task_token, true) &&
                back->snapshot().page_id == "detail" && back->snapshot().back_pending,
            "old task approval must not affect the new task");
    require(back->complete_back(pending_new_task->value(), true).has_value() &&
                back->snapshot().page_id == "root",
            "current task approval should pop exactly one Page");

    auto missing_owned_control = PageNavigator::create(
        PageDeclaration{
            .app_id = "app.owned",
            .root_page_id = "root",
            .page_ids = {"root", "detail"},
            .back_presentation = BackPresentation::AppOwned,
        },
        [](std::string_view, std::string_view) { return true; }
    );
    require(!missing_owned_control &&
                missing_owned_control.error() == NavigationError::InvalidDeclaration,
            "multi-Page appOwned declaration must provide a visible Back control");

    auto owned = PageNavigator::create(
        PageDeclaration{
            .app_id = "app.owned",
            .root_page_id = "root",
            .page_ids = {"root", "detail"},
            .back_presentation = BackPresentation::AppOwned,
            .has_app_owned_back_control = true,
        },
        [](std::string_view, std::string_view) { return true; }
    );
    require(owned && owned->start() && owned->push("detail"),
            "multi-Page appOwned declaration should install with visible Back");
    require(!owned->show_default_back() && !owned->edge_back_enabled(),
            "appOwned must disable both framework Back entry points");

    auto standard = PageNavigator::create(
        PageDeclaration{
            .app_id = "app.standard",
            .root_page_id = "root",
            .page_ids = {"root", "detail"},
            .uses_standard_back_control = true,
        },
        [](std::string_view, std::string_view) { return true; }
    );
    require(standard && standard->start() && standard->push("detail"),
            "standard-control declaration should install");
    require(!standard->show_default_back() && standard->edge_back_enabled(),
            "standard Back control should suppress duplicate overlay but retain Edge Back");

    bool default_visible = false;
    bool edge_enabled = false;
    back->set_availability_handler([&](bool visible, bool edge) {
        default_visible = visible;
        edge_enabled = edge;
    });
    require(!default_visible && !edge_enabled, "Root should publish no Back entry point");
    require(back->push("detail").has_value(), "Detail should reopen for availability check");
    require(default_visible && edge_enabled,
            "child Page should publish both default Back entry points");
    back->set_back_handler([](const auto &, uint64_t) { return BackDecision::Cancel; });
    auto cancelled = back->request_back(1200);
    require(!cancelled && cancelled.error() == NavigationError::BackCancelled &&
                default_visible && edge_enabled,
            "immediate cancellation should preserve child Back availability");
    back->stop();
    require(!default_visible && !edge_enabled, "stopping App should hide Back entry points");

    auto concurrent = PageNavigator::create(
        PageDeclaration{
            .app_id = "app.concurrent",
            .root_page_id = "root",
            .page_ids = {"root", "detail"},
        },
        [](std::string_view, std::string_view) { return true; }
    );
    require(concurrent && concurrent->start() && concurrent->push("detail"),
            "concurrent Back fixture should open Detail");
    std::promise<void> entered;
    std::promise<void> release;
    auto released = release.get_future();
    concurrent->set_back_handler([&](const auto &, uint64_t) {
        entered.set_value();
        released.wait();
        return BackDecision::Allow;
    });
    auto requested = std::async(std::launch::async, [&] {
        return concurrent->request_back(1300);
    });
    entered.get_future().wait();
    auto stopped = std::async(std::launch::async, [&] {
        concurrent->stop();
    });
    const auto stop_status = stopped.wait_for(std::chrono::seconds(1));
    release.set_value();
    stopped.wait();
    auto after_stop = requested.get();
    require(stop_status == std::future_status::ready,
            "PWR Home must not wait for an App Back callback");
    require(!after_stop && after_stop.error() == NavigationError::StaleRequest &&
                concurrent->snapshot().page_id.empty(),
            "an App Back answer after stop must not restore a stale Page");
}
