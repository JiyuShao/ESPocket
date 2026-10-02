#include "espocket/card_session.hpp"

#include <cassert>
#include <string>
#include <vector>

using namespace espocket;

struct Content final : CardContent {
    std::vector<std::string> &events;
    bool &show_ok;
    bool &refresh_ok;
    Content(std::vector<std::string> &log, bool &show_result, bool &refresh_result)
        : events(log), show_ok(show_result), refresh_ok(refresh_result) {}
    ~Content() override { events.push_back("destroy"); }
    bool show() noexcept override { events.push_back("show"); return show_ok; }
    bool refresh() noexcept override { events.push_back("refresh"); return refresh_ok; }
    void pause() noexcept override { events.push_back("pause"); }
};

int main()
{
    CardRegistry registry;
    PageDeclaration declaration{"app", "root", {"root", "detail"}, {{"a", "detail"}, {"b", ""}}};
    assert(registry.register_app(declaration));
    const CardKey a{"app", "a"}, b{"app", "b"};
    std::vector<std::string> events;
    bool create_ok = true, show_ok = true, refresh_ok = true;
    CardSession *owner = nullptr;
    CardSession session(registry, [&](const CardKey &) -> std::unique_ptr<CardContent> {
        events.push_back("create");
        assert(owner->release().error() == CardSessionError::Busy);
        if (!create_ok) return nullptr;
        return std::make_unique<Content>(events, show_ok, refresh_ok);
    });
    owner = &session;
    registry.set_removal_handler([&](const auto &removed) { assert(session.invalidate(removed.key)); });
    assert(session.open_app({}).error() == CardSessionError::NoCard);
    assert(session.show(a).error() == CardSessionError::NotConfigured);
    assert(events.empty() && session.visibility() == CardVisibility::Empty);
    assert(registry.add(a, CardSide::Left, 0));
    assert(registry.add(b, CardSide::Right, 0));
    create_ok = false;
    assert(session.show(a).error() == CardSessionError::CreationFailed);
    assert(!session.key() && session.visibility() == CardVisibility::Empty);
    create_ok = true;
    events.clear();
    assert(session.show(a));
    assert(events == std::vector<std::string>({"create", "show", "refresh"}));
    assert(session.key() == a && session.visibility() == CardVisibility::Visible);
    assert(session.show(a)); // Already visible is not another visibility transition.
    assert(events.size() == 3);
    assert(session.pause());
    assert(session.pause());
    assert(events.back() == "pause" && events.size() == 4);
    assert(session.show(a)); // Resume retained UI, always request fresh data.
    assert(events == std::vector<std::string>({"create", "show", "refresh", "pause", "show", "refresh"}));
    events.clear();
    assert(session.show(b));
    assert(events == std::vector<std::string>({"pause", "destroy", "create", "show", "refresh"}));
    assert(session.open_app([&](const auto &key, auto target) {
        assert(key == b && target == "root");
        assert(session.visibility() == CardVisibility::Paused && events.back() == "pause");
        assert(session.show(a).error() == CardSessionError::Busy);
        events.push_back("launch");
        return true;
    }));
    assert(session.visibility() == CardVisibility::Paused);
    assert(session.show(b));
    assert(session.open_app([](const auto &, auto) { return false; }).error() == CardSessionError::LaunchFailed);
    assert(session.visibility() == CardVisibility::Paused); // Shell explicitly re-shows on launch failure.
    assert(session.release());
    assert(session.release());
    assert(!session.key() && session.visibility() == CardVisibility::Empty);
    show_ok = false;
    events.clear();
    assert(session.show(a).error() == CardSessionError::PresentationFailed);
    assert(events == std::vector<std::string>({"create", "show", "pause"}));
    assert(session.visibility() == CardVisibility::Paused);
    show_ok = true;
    refresh_ok = false;
    assert(session.show(a).error() == CardSessionError::RefreshFailed);
    assert(session.visibility() == CardVisibility::Paused && events.back() == "pause");
    refresh_ok = true;
    assert(session.show(a));
    declaration.cards[0].target_page_id = "root";
    assert(registry.update_app(declaration));
    assert(session.open_app([](const auto &, auto target) { return target == "root"; }));
    assert(session.show(a));
    assert(session.invalidate(b)); // Removing another Card cannot free this one.
    assert(session.visibility() == CardVisibility::Visible);
    assert(registry.remove(a));
    assert(!session.key() && events.back() == "destroy");
    assert(session.show(a).error() == CardSessionError::NotConfigured);
    assert(session.show(b));
    declaration.cards = {{"a", "root"}};
    assert(registry.update_app(declaration));
    assert(session.visibility() == CardVisibility::Empty && events.back() == "destroy");
    assert(session.show(b).error() == CardSessionError::DeclarationUnavailable);

    // Even if removal notification wiring is missing, an invalid launch releases old UI.
    registry.set_removal_handler({});
    assert(registry.add(a, CardSide::Left, 0));
    assert(session.show(a));
    assert(registry.remove(a));
    bool launched = false;
    assert(session.open_app([&](const auto &, auto) { launched = true; return true; }).error() ==
           CardSessionError::NotConfigured);
    assert(!launched && session.visibility() == CardVisibility::Empty);
    assert(registry.add(a, CardSide::Left, 0));
    assert(session.show(a));
    assert(registry.uninstall_app("app"));
    assert(session.open_app({}).error() == CardSessionError::DeclarationUnavailable);
    assert(session.visibility() == CardVisibility::Empty);

    // Scope exit pauses visible work before freeing UI/subscriptions.
    assert(registry.register_app(declaration));
    assert(registry.add(a, CardSide::Left, 0));
    events.clear();
    {
        CardSession scoped(registry, [&](const auto &) {
            return std::make_unique<Content>(events, show_ok, refresh_ok);
        });
        assert(scoped.show(a));
    }
    assert(events == std::vector<std::string>({"show", "refresh", "pause", "destroy"}));
}
