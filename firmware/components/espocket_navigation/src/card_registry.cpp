#include "espocket/card_registry.hpp"

#include <algorithm>
#include <set>
#include <utility>

namespace espocket {

std::expected<void, CardError> CardRegistry::register_app(PageDeclaration declaration)
{
    if (!validate_page_declaration(declaration)) { return std::unexpected(CardError::InvalidDeclaration); }
    std::lock_guard lock(mutex_);
    if (declarations_.contains(declaration.app_id)) { return std::unexpected(CardError::AlreadyRegistered); }
    const auto id = declaration.app_id;
    declarations_.emplace(id, std::move(declaration));
    return {};
}

std::expected<void, CardError> CardRegistry::update_app(PageDeclaration declaration)
{
    if (!validate_page_declaration(declaration)) { return std::unexpected(CardError::InvalidDeclaration); }
    std::vector<CardRemoval> removed;
    RemovalHandler handler;
    {
        std::lock_guard lock(mutex_);
        auto previous = declarations_.find(declaration.app_id);
        if (previous == declarations_.end()) { return std::unexpected(CardError::UnknownApp); }
        if (previous->second.root_page_id != declaration.root_page_id) {
            return std::unexpected(CardError::IdentityMismatch);
        }
        previous->second = std::move(declaration);
        removed = prune_locked(previous->first, CardRemovalReason::RemovedByUpdate);
        handler = removal_handler_;
    }
    if (handler) { for (const auto &event : removed) { handler(event); } }
    return {};
}

std::expected<void, CardError> CardRegistry::uninstall_app(std::string_view app_id)
{
    std::vector<CardRemoval> removed;
    RemovalHandler handler;
    {
        std::lock_guard lock(mutex_);
        auto previous = declarations_.find(app_id);
        if (previous == declarations_.end()) { return std::unexpected(CardError::UnknownApp); }
        const auto id = previous->first;
        declarations_.erase(previous);
        removed = prune_locked(id, CardRemovalReason::AppUninstalled);
        handler = removal_handler_;
    }
    if (handler) { for (const auto &event : removed) { handler(event); } }
    return {};
}

std::vector<CardRemoval> CardRegistry::prune_locked(std::string_view app_id, CardRemovalReason reason)
{
    std::vector<CardRemoval> removed;
    for (auto *side : {&configuration_.left, &configuration_.right}) {
        std::erase_if(*side, [&](const auto &key) {
            if (key.app_id != app_id || target_page_locked(key)) { return false; }
            removed.push_back({key, reason});
            return true;
        });
    }
    return removed;
}

std::vector<CardKey> CardRegistry::available_cards() const
{
    std::lock_guard lock(mutex_);
    std::vector<CardKey> cards;
    for (const auto &[app_id, declaration] : declarations_) {
        for (const auto &card : declaration.cards) { cards.push_back({app_id, card.card_id}); }
    }
    return cards;
}

std::expected<std::string, CardError> CardRegistry::target_page_locked(const CardKey &key) const
{
    auto app = declarations_.find(key.app_id);
    if (app == declarations_.end()) { return std::unexpected(CardError::UnknownApp); }
    auto card = std::ranges::find_if(app->second.cards, [&](const auto &entry) {
        return entry.card_id == key.card_id;
    });
    if (card == app->second.cards.end()) { return std::unexpected(CardError::UnknownCard); }
    return card->target_page_id.empty() ? app->second.root_page_id : card->target_page_id;
}

std::expected<std::string, CardError> CardRegistry::target_page(const CardKey &key) const
{
    std::lock_guard lock(mutex_);
    return target_page_locked(key);
}

std::vector<CardKey> &CardRegistry::side_locked(CardSide side)
{
    return side == CardSide::Left ? configuration_.left : configuration_.right;
}

std::expected<void, CardError> CardRegistry::add(const CardKey &key, CardSide side, size_t index)
{
    if (side != CardSide::Left && side != CardSide::Right) { return std::unexpected(CardError::InvalidSide); }
    std::lock_guard lock(mutex_);
    auto target = target_page_locked(key);
    if (!target) { return std::unexpected(target.error()); }
    if (std::ranges::find(configuration_.left, key) != configuration_.left.end() ||
            std::ranges::find(configuration_.right, key) != configuration_.right.end()) {
        return std::unexpected(CardError::AlreadyConfigured);
    }
    auto &sequence = side_locked(side);
    if (index > sequence.size()) { return std::unexpected(CardError::InvalidPosition); }
    sequence.insert(sequence.begin() + index, key);
    return {};
}

std::expected<void, CardError> CardRegistry::move(const CardKey &key, CardSide side, size_t final_index)
{
    if (side != CardSide::Left && side != CardSide::Right) { return std::unexpected(CardError::InvalidSide); }
    std::lock_guard lock(mutex_);
    auto &destination = side_locked(side);
    for (auto *source : {&configuration_.left, &configuration_.right}) {
        auto found = std::ranges::find(*source, key);
        if (found == source->end()) { continue; }
        const auto final_size = destination.size() - (source == &destination ? 1 : 0);
        if (final_index > final_size) { return std::unexpected(CardError::InvalidPosition); }
        const auto copy = *found;
        source->erase(found);
        destination.insert(destination.begin() + final_index, copy);
        return {};
    }
    return std::unexpected(CardError::NotConfigured);
}

std::expected<void, CardError> CardRegistry::remove(const CardKey &key)
{
    RemovalHandler handler;
    bool removed = false;
    {
        std::lock_guard lock(mutex_);
        for (auto *side : {&configuration_.left, &configuration_.right}) {
            removed = std::erase(*side, key) > 0 || removed;
        }
        handler = removal_handler_;
    }
    if (!removed) { return std::unexpected(CardError::NotConfigured); }
    if (handler) { handler({key, CardRemovalReason::UserRemoved}); }
    return {};
}

std::expected<void, CardError> CardRegistry::replace_configuration(CardConfiguration configuration)
{
    std::vector<CardRemoval> removed;
    RemovalHandler handler;
    {
        std::lock_guard lock(mutex_);
        if (auto valid = validate_configuration_locked(configuration); !valid) return valid;
        std::set<std::pair<std::string, std::string>> seen;
        for (const auto *side : {&configuration.left, &configuration.right}) {
            for (const auto &key : *side) {
                seen.emplace(key.app_id, key.card_id);
            }
        }
        for (const auto *side : {&configuration_.left, &configuration_.right}) {
            for (const auto &key : *side) {
                if (!seen.contains({key.app_id, key.card_id})) {
                    removed.push_back({key, CardRemovalReason::UserRemoved});
                }
            }
        }
        configuration_ = std::move(configuration);
        handler = removal_handler_;
    }
    if (handler) { for (const auto &event : removed) { handler(event); } }
    return {};
}

std::expected<void, CardError> CardRegistry::validate_configuration_locked(const CardConfiguration &configuration) const
{
    std::set<std::pair<std::string, std::string>> seen;
    for (const auto *side : {&configuration.left, &configuration.right}) {
        for (const auto &key : *side) {
            auto target = target_page_locked(key);
            if (!target) return std::unexpected(target.error());
            if (!seen.emplace(key.app_id, key.card_id).second) return std::unexpected(CardError::AlreadyConfigured);
        }
    }
    return {};
}

std::expected<void, CardError> CardRegistry::validate_configuration(const CardConfiguration &configuration) const
{
    std::lock_guard lock(mutex_);
    return validate_configuration_locked(configuration);
}

CardConfiguration CardRegistry::configuration() const
{
    std::lock_guard lock(mutex_);
    return configuration_;
}

void CardRegistry::set_removal_handler(RemovalHandler handler)
{
    std::lock_guard lock(mutex_);
    removal_handler_ = std::move(handler);
}

} // namespace espocket
