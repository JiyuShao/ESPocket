#include "espocket/card_registry.hpp"

#include <algorithm>
#include <cassert>

using namespace espocket;

int main()
{
    PageDeclaration first{"app.a", "root", {"root", "detail"}, {{"summary", ""}, {"control", "detail"}}};
    auto second = first;
    second.app_id = "app.b";
    CardRegistry registry;
    assert(registry.register_app(first));
    assert(registry.register_app(second));
    assert(registry.available_cards().size() == 4);
    assert(registry.register_app(first).error() == CardError::AlreadyRegistered);
    auto invalid = first;
    invalid.app_id = "app.invalid";
    invalid.cards.push_back({"invalid", "missing"});
    assert(registry.register_app(invalid).error() == CardError::InvalidDeclaration);
    assert(registry.available_cards().size() == 4);
    const CardKey a{"app.a", "summary"}, b{"app.a", "control"}, c{"app.b", "summary"};
    assert(registry.declaration("app.a")->cards.size() == 2);
    assert(registry.declaration("missing").error() == CardError::UnknownApp);
    assert(registry.target_page(a) == "root");
    assert(registry.target_page(b) == "detail");
    assert(registry.add(a, CardSide::Left, 0));
    assert(registry.add(b, CardSide::Left, 1));
    assert(registry.add(c, CardSide::Right, 0));
    assert(registry.add(a, CardSide::Right, 0).error() == CardError::AlreadyConfigured);
    assert(registry.add({"missing", "summary"}, CardSide::Left, 0).error() == CardError::UnknownApp);
    assert(registry.add({"app.a", "missing"}, CardSide::Left, 0).error() == CardError::UnknownCard);
    const auto initial = registry.configuration();
    assert(registry.move(b, CardSide::Left, 3).error() == CardError::InvalidPosition);
    assert(registry.move(b, static_cast<CardSide>(99), 0).error() == CardError::InvalidSide);
    assert(registry.configuration() == initial);
    assert(registry.move(b, CardSide::Left, 0));
    assert(registry.configuration().left == std::vector<CardKey>({b, a}));
    assert(registry.move(a, CardSide::Right, 1));
    assert(registry.configuration().left == std::vector<CardKey>({b}));
    assert(registry.configuration().right == std::vector<CardKey>({c, a}));
    const auto reordered = registry.configuration();
    auto duplicate = reordered;
    duplicate.left.push_back(a);
    assert(registry.replace_configuration(duplicate).error() == CardError::AlreadyConfigured);
    auto unknown = reordered;
    unknown.right.push_back({"app.b", "missing"});
    assert(registry.replace_configuration(unknown).error() == CardError::UnknownCard);
    assert(registry.configuration() == reordered);
    assert(registry.replace_configuration(initial));
    assert(registry.configuration() == initial);

    std::vector<CardRemoval> removed;
    registry.set_removal_handler([&](const auto &event) {
        // Notifications run after commit and outside the mutex: reading the Owner is safe.
        auto current = registry.configuration();
        assert(std::ranges::find(current.left, event.key) == current.left.end());
        assert(std::ranges::find(current.right, event.key) == current.right.end());
        removed.push_back(event);
    });
    auto updated = first;
    std::reverse(updated.cards.begin(), updated.cards.end());
    assert(registry.update_app(updated));
    assert(registry.configuration() == initial && removed.empty());
    updated.cards[0].target_page_id = "root";
    assert(registry.update_app(updated));
    assert(registry.target_page(b) == "root" && registry.configuration() == initial);
    auto bad_update = updated;
    bad_update.cards.push_back({"summary", "root"});
    assert(registry.update_app(bad_update).error() == CardError::InvalidDeclaration);
    assert(registry.configuration() == initial && removed.empty());
    bad_update = updated;
    bad_update.root_page_id = "detail";
    assert(registry.update_app(bad_update).error() == CardError::IdentityMismatch);
    updated.cards = {{"control", "detail"}};
    assert(registry.update_app(updated));
    assert(registry.configuration().left == std::vector<CardKey>({b}));
    assert(registry.configuration().right == std::vector<CardKey>({c}));
    assert(removed.size() == 1 && removed[0].key == a &&
           removed[0].reason == CardRemovalReason::RemovedByUpdate);
    assert(registry.add(a, CardSide::Left, 0).error() == CardError::UnknownCard);
    assert(registry.uninstall_app("app.a"));
    assert(registry.configuration().left.empty() && registry.configuration().right == std::vector<CardKey>({c}));
    assert(removed.size() == 2 && removed[1].key == b &&
           removed[1].reason == CardRemovalReason::AppUninstalled);
    assert(registry.target_page(b).error() == CardError::UnknownApp);
    assert(registry.remove(c));
    assert(removed.size() == 3 && removed[2].reason == CardRemovalReason::UserRemoved);
    assert(registry.remove(c).error() == CardError::NotConfigured && removed.size() == 3);
    assert(registry.available_cards().size() == 2); // App B still installed, configuration is optional.
    assert(registry.add(c, CardSide::Right, 0));
    assert(registry.replace_configuration({}));
    assert(removed.size() == 4 && removed[3].key == c &&
           removed[3].reason == CardRemovalReason::UserRemoved);
    assert(registry.uninstall_app("app.b"));
    assert(registry.available_cards().empty());
}
