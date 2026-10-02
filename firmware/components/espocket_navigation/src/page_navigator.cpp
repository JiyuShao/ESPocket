#include "espocket/page_navigator.hpp"

#include <algorithm>
#include <unordered_set>
#include <utility>

namespace espocket {

PageNavigator::PageNavigator(PageDeclaration declaration, Presenter presenter)
    : declaration_(std::move(declaration)), presenter_(std::move(presenter))
{}

std::expected<void, NavigationError> validate_page_declaration(const PageDeclaration &declaration)
{
    if (declaration.app_id.empty() || declaration.root_page_id.empty()) {
        return std::unexpected(NavigationError::InvalidDeclaration);
    }
    std::unordered_set<std::string_view> pages;
    for (const auto &page : declaration.page_ids) {
        if (page.empty() || !pages.insert(page).second) {
            return std::unexpected(NavigationError::InvalidDeclaration);
        }
    }
    if (!pages.contains(declaration.root_page_id)) {
        return std::unexpected(NavigationError::InvalidDeclaration);
    }
    std::unordered_set<std::string_view> cards;
    for (const auto &card : declaration.cards) {
        if (card.card_id.empty() || !cards.insert(card.card_id).second ||
                (!card.target_page_id.empty() && !pages.contains(card.target_page_id))) {
            return std::unexpected(NavigationError::InvalidDeclaration);
        }
    }
    return {};
}

std::expected<PageNavigator, NavigationError> PageNavigator::create(
    PageDeclaration declaration, Presenter presenter)
{
    if (!presenter) { return std::unexpected(NavigationError::InvalidDeclaration); }
    auto validated = validate_page_declaration(declaration);
    if (!validated) { return std::unexpected(validated.error()); }
    return PageNavigator(std::move(declaration), std::move(presenter));
}

bool PageNavigator::declares(std::string_view page_id) const
{
    std::lock_guard lock(*mutex_);
    return std::ranges::any_of(declaration_.page_ids, [page_id](const auto &declared) {
        return declared == page_id;
    });
}

std::expected<void, NavigationError> PageNavigator::present(std::string_view to)
{
    std::lock_guard lock(*mutex_);
    const std::string_view from = stack_.empty() ? std::string_view{} : stack_.back();
    if (!presenter_(from, to)) {
        return std::unexpected(NavigationError::PresentationFailed);
    }
    return {};
}

std::expected<void, NavigationError> PageNavigator::start()
{
    std::lock_guard lock(*mutex_);
    if (!stack_.empty()) {
        return std::unexpected(NavigationError::InvalidDeclaration);
    }
    auto result = present(declaration_.root_page_id);
    if (!result) {
        return result;
    }
    stack_.push_back(declaration_.root_page_id);
    publish_availability();
    return {};
}

std::expected<void, NavigationError> PageNavigator::start_from_card(std::string_view card_id)
{
    std::unique_lock lock(*mutex_);
    auto started = start();
    if (!started) {
        return started;
    }
    const auto card = std::ranges::find_if(declaration_.cards, [card_id](const auto &candidate) {
        return candidate.card_id == card_id;
    });
    if (card == declaration_.cards.end()) {
        auto diagnostic = diagnostic_handler_;
        lock.unlock();
        if (diagnostic) {
            diagnostic(NavigationError::TargetUnavailable, card_id);
        }
        return std::unexpected(NavigationError::TargetUnavailable);
    }
    if (card->target_page_id.empty() || card->target_page_id == declaration_.root_page_id) {
        return {};
    }
    auto opened = push(card->target_page_id);
    if (!opened) {
        auto diagnostic = diagnostic_handler_;
        lock.unlock();
        if (diagnostic) {
            diagnostic(NavigationError::TargetUnavailable, card_id);
        }
        return std::unexpected(NavigationError::TargetUnavailable);
    }
    return {};
}

std::expected<void, NavigationError> PageNavigator::push(std::string_view page_id)
{
    std::lock_guard lock(*mutex_);
    if (stack_.empty()) {
        return std::unexpected(NavigationError::NotStarted);
    }
    if (!declares(page_id)) {
        return std::unexpected(NavigationError::UnknownPage);
    }
    if (page_id == declaration_.root_page_id) {
        return std::unexpected(NavigationError::RootPage);
    }
    auto result = present(page_id);
    if (!result) {
        return result;
    }
    stack_.emplace_back(page_id);
    pending_back_.reset();
    publish_availability();
    return {};
}

std::expected<void, NavigationError> PageNavigator::pop()
{
    std::lock_guard lock(*mutex_);
    if (stack_.empty()) {
        return std::unexpected(NavigationError::NotStarted);
    }
    if (stack_.size() == 1) {
        return std::unexpected(NavigationError::AtRoot);
    }
    auto result = present(stack_[stack_.size() - 2]);
    if (!result) {
        return result;
    }
    stack_.pop_back();
    pending_back_.reset();
    publish_availability();
    return {};
}

std::expected<void, NavigationError> PageNavigator::replace(std::string_view page_id)
{
    std::lock_guard lock(*mutex_);
    if (stack_.empty()) {
        return std::unexpected(NavigationError::NotStarted);
    }
    if (stack_.size() == 1) {
        return std::unexpected(NavigationError::AtRoot);
    }
    if (!declares(page_id)) {
        return std::unexpected(NavigationError::UnknownPage);
    }
    if (page_id == declaration_.root_page_id) {
        return std::unexpected(NavigationError::RootPage);
    }
    auto result = present(page_id);
    if (!result) {
        return result;
    }
    stack_.back() = page_id;
    pending_back_.reset();
    publish_availability();
    return {};
}

std::expected<void, NavigationError> PageNavigator::reset_to_root()
{
    std::lock_guard lock(*mutex_);
    if (stack_.empty()) {
        return std::unexpected(NavigationError::NotStarted);
    }
    if (stack_.size() == 1) {
        return {};
    }
    auto result = present(declaration_.root_page_id);
    if (!result) {
        return result;
    }
    stack_.resize(1);
    pending_back_.reset();
    publish_availability();
    return {};
}

std::expected<void, NavigationError> PageNavigator::update_declaration(PageDeclaration declaration)
{
    std::lock_guard lock(*mutex_);
    if (!stack_.empty()) {
        return std::unexpected(NavigationError::DeclarationInUse);
    }
    if (declaration.app_id != declaration_.app_id ||
            declaration.root_page_id != declaration_.root_page_id) {
        return std::unexpected(NavigationError::IdentityMismatch);
    }
    auto validated = validate_page_declaration(declaration);
    if (!validated) {
        return std::unexpected(validated.error());
    }
    declaration_ = std::move(declaration);
    publish_availability();
    return {};
}

void PageNavigator::set_back_handler(BackHandler handler)
{
    std::lock_guard lock(*mutex_);
    back_handler_ = std::move(handler);
}

void PageNavigator::set_availability_handler(AvailabilityHandler handler)
{
    std::lock_guard lock(*mutex_);
    availability_handler_ = std::move(handler);
    publish_availability();
}

void PageNavigator::set_diagnostic_handler(DiagnosticHandler handler)
{
    std::lock_guard lock(*mutex_);
    diagnostic_handler_ = std::move(handler);
}

std::expected<std::optional<uint64_t>, NavigationError> PageNavigator::request_back(
    uint64_t now_ms
)
{
    std::unique_lock lock(*mutex_);
    if (stack_.empty()) {
        return std::unexpected(NavigationError::NotStarted);
    }
    if (pending_back_) {
        return std::unexpected(NavigationError::BackPending);
    }
    if (stack_.size() == 1) {
        return std::unexpected(NavigationError::AtRoot);
    }
    if (!back_handler_) {
        auto result = pop();
        if (!result) {
            return std::unexpected(result.error());
        }
        return std::optional<uint64_t>{};
    }

    const auto token = next_back_token_++;
    const auto current = snapshot();
    const auto handler = back_handler_;
    pending_back_ = PendingBack{token, now_ms};
    publish_availability();
    lock.unlock();
    const auto decision = handler(current, token);
    lock.lock();
    if (!pending_back_ || pending_back_->token != token) {
        return std::unexpected(NavigationError::StaleRequest);
    }
    switch (decision) {
    case BackDecision::Cancel:
        pending_back_.reset();
        publish_availability();
        return std::unexpected(NavigationError::BackCancelled);
    case BackDecision::Defer:
        return std::optional<uint64_t>{token};
    case BackDecision::Allow:
        pending_back_.reset();
        auto result = pop();
        if (!result) {
            publish_availability();
            return std::unexpected(result.error());
        }
        return std::optional<uint64_t>{};
    }
    return std::unexpected(NavigationError::BackCancelled);
}

std::expected<void, NavigationError> PageNavigator::complete_back(uint64_t token, bool allow)
{
    std::lock_guard lock(*mutex_);
    if (!pending_back_ || pending_back_->token != token) {
        return std::unexpected(NavigationError::StaleRequest);
    }
    pending_back_.reset();
    if (!allow) {
        publish_availability();
        return {};
    }
    auto result = pop();
    if (!result) {
        publish_availability();
    }
    return result;
}

std::optional<NavigationError> PageNavigator::expire_back(uint64_t now_ms)
{
    std::lock_guard lock(*mutex_);
    if (!pending_back_ || now_ms < pending_back_->started_ms ||
            now_ms - pending_back_->started_ms < BACK_TIMEOUT_MS) {
        return std::nullopt;
    }
    pending_back_.reset();
    publish_availability();
    return NavigationError::BackTimeout;
}

void PageNavigator::stop()
{
    std::lock_guard lock(*mutex_);
    stack_.clear();
    pending_back_.reset();
    publish_availability();
}

PageSnapshot PageNavigator::snapshot() const
{
    std::lock_guard lock(*mutex_);
    return {
        .app_id = declaration_.app_id,
        .page_id = stack_.empty() ? "" : stack_.back(),
        .can_back = stack_.size() > 1 && !pending_back_,
        .back_pending = pending_back_.has_value(),
    };
}

bool PageNavigator::show_default_back() const
{
    std::lock_guard lock(*mutex_);
    return snapshot().can_back && declaration_.back_presentation == BackPresentation::Framework &&
           !declaration_.uses_standard_back_control;
}

bool PageNavigator::edge_back_enabled() const
{
    std::lock_guard lock(*mutex_);
    return snapshot().can_back && declaration_.back_presentation == BackPresentation::Framework;
}

bool PageNavigator::framework_owns_back() const
{
    std::lock_guard lock(*mutex_);
    return !stack_.empty() && declaration_.back_presentation == BackPresentation::Framework;
}

void PageNavigator::publish_availability() const
{
    std::lock_guard lock(*mutex_);
    if (availability_handler_) {
        availability_handler_(show_default_back(), edge_back_enabled());
    }
}

} // namespace espocket
