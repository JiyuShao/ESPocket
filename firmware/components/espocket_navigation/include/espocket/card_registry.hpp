#pragma once

#include <cstddef>
#include <expected>
#include <functional>
#include <map>
#include <mutex>
#include <string>
#include <string_view>
#include <vector>

#include "espocket/page_navigator.hpp"

namespace espocket {

struct CardKey {
    std::string app_id;
    std::string card_id;
    bool operator==(const CardKey &) const = default;
};

enum class CardSide { Left, Right };
enum class CardError {
    InvalidDeclaration, UnknownApp, UnknownCard, AlreadyRegistered, AlreadyConfigured,
    NotConfigured, InvalidPosition, InvalidSide, IdentityMismatch,
};
enum class CardRemovalReason { UserRemoved, AppUninstalled, RemovedByUpdate };

struct CardRemoval {
    CardKey key;
    CardRemovalReason reason;
};

struct CardConfiguration {
    std::vector<CardKey> left;
    std::vector<CardKey> right;
    bool operator==(const CardConfiguration &) const = default;
};

// Home Space configuration only. Does not hold App runtime state, Page stacks, or GUI objects.
class CardRegistry {
public:
    using RemovalHandler = std::function<void(const CardRemoval &)>;
    std::expected<void, CardError> register_app(PageDeclaration declaration);
    std::expected<void, CardError> update_app(PageDeclaration declaration);
    std::expected<void, CardError> uninstall_app(std::string_view app_id);
    std::vector<CardKey> available_cards() const;
    std::expected<PageDeclaration, CardError> declaration(std::string_view app_id) const;
    std::expected<std::string, CardError> target_page(const CardKey &key) const;
    std::expected<void, CardError> add(const CardKey &key, CardSide side, size_t index);
    std::expected<void, CardError> move(const CardKey &key, CardSide side, size_t final_index);
    std::expected<void, CardError> remove(const CardKey &key);
    std::expected<void, CardError> replace_configuration(CardConfiguration configuration);
    std::expected<void, CardError> validate_configuration(const CardConfiguration &configuration) const;
    CardConfiguration configuration() const;
    void set_removal_handler(RemovalHandler handler);

private:
    std::expected<void, CardError> validate_configuration_locked(const CardConfiguration &configuration) const;
    std::expected<std::string, CardError> target_page_locked(const CardKey &key) const;
    std::vector<CardKey> &side_locked(CardSide side);
    std::vector<CardRemoval> prune_locked(std::string_view app_id, CardRemovalReason reason);
    mutable std::mutex mutex_;
    std::map<std::string, PageDeclaration, std::less<>> declarations_;
    CardConfiguration configuration_;
    RemovalHandler removal_handler_;
};

} // namespace espocket
