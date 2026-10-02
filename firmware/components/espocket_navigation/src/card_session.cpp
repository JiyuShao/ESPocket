#include "espocket/card_session.hpp"

#include <algorithm>
#include <utility>

namespace espocket {
namespace {
struct Operation {
    bool &busy;
    explicit Operation(bool &flag) : busy(flag) { busy = true; }
    ~Operation() { busy = false; }
};
}

CardSession::CardSession(CardRegistry &registry, Factory factory)
    : registry_(registry), factory_(std::move(factory)) {}

CardSession::~CardSession()
{
    busy_ = true;
    release_content();
}

void CardSession::pause_content()
{
    if (visibility_ == CardVisibility::Visible) {
        visibility_ = CardVisibility::Paused;
        content_->pause();
    }
}

void CardSession::release_content()
{
    pause_content();
    visibility_ = CardVisibility::Empty;
    key_.reset();
    content_.reset();
}

std::expected<void, CardSessionError> CardSession::show(const CardKey &key)
{
    if (busy_) return std::unexpected(CardSessionError::Busy);
    Operation operation(busy_);
    if (!registry_.target_page(key)) return std::unexpected(CardSessionError::DeclarationUnavailable);
    const auto configuration = registry_.configuration();
    if (std::ranges::find(configuration.left, key) == configuration.left.end() &&
        std::ranges::find(configuration.right, key) == configuration.right.end()) {
        return std::unexpected(CardSessionError::NotConfigured);
    }
    if (key_ != key) {
        release_content();
        content_ = factory_ ? factory_(key) : nullptr;
        if (!content_) return std::unexpected(CardSessionError::CreationFailed);
        key_ = key;
        visibility_ = CardVisibility::Paused;
    }
    if (visibility_ == CardVisibility::Visible) return {};
    if (!content_->show()) {
        // A failed presenter may have partially created visible work.
        content_->pause();
        return std::unexpected(CardSessionError::PresentationFailed);
    }
    visibility_ = CardVisibility::Visible;
    if (!content_->refresh()) {
        pause_content();
        return std::unexpected(CardSessionError::RefreshFailed);
    }
    return {};
}

std::expected<void, CardSessionError> CardSession::pause()
{
    if (busy_) return std::unexpected(CardSessionError::Busy);
    Operation operation(busy_);
    pause_content();
    return {};
}

std::expected<void, CardSessionError> CardSession::release()
{
    if (busy_) return std::unexpected(CardSessionError::Busy);
    Operation operation(busy_);
    release_content();
    return {};
}

std::expected<void, CardSessionError> CardSession::invalidate(const CardKey &key)
{
    if (busy_) return std::unexpected(CardSessionError::Busy);
    Operation operation(busy_);
    if (key_ == key) release_content();
    return {};
}

std::expected<void, CardSessionError> CardSession::open_app(const AppLauncher &launcher)
{
    if (busy_) return std::unexpected(CardSessionError::Busy);
    Operation operation(busy_);
    if (!key_) return std::unexpected(CardSessionError::NoCard);
    const auto target = registry_.target_page(*key_);
    if (!target) {
        release_content();
        return std::unexpected(CardSessionError::DeclarationUnavailable);
    }
    const auto configuration = registry_.configuration();
    if (std::ranges::find(configuration.left, *key_) == configuration.left.end() &&
        std::ranges::find(configuration.right, *key_) == configuration.right.end()) {
        release_content();
        return std::unexpected(CardSessionError::NotConfigured);
    }
    pause_content();
    if (!launcher || !launcher(*key_, *target)) return std::unexpected(CardSessionError::LaunchFailed);
    return {};
}

std::expected<void, CardSessionError> CardSession::action(std::string_view action)
{
    if (busy_) return std::unexpected(CardSessionError::Busy);
    Operation operation(busy_);
    if (!key_ || visibility_ != CardVisibility::Visible) return std::unexpected(CardSessionError::NoCard);
    if (!registry_.target_page(*key_)) {
        release_content();
        return std::unexpected(CardSessionError::DeclarationUnavailable);
    }
    const auto configuration = registry_.configuration();
    if (std::ranges::find(configuration.left, *key_) == configuration.left.end() &&
        std::ranges::find(configuration.right, *key_) == configuration.right.end()) {
        release_content();
        return std::unexpected(CardSessionError::NotConfigured);
    }
    return content_->action(action) ? std::expected<void, CardSessionError>{} :
                                    std::unexpected(CardSessionError::PresentationFailed);
}

} // namespace espocket
