#pragma once

#include <expected>
#include <cstdint>
#include <functional>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace espocket {

enum class NavigationError {
    InvalidDeclaration,
    NotStarted,
    UnknownPage,
    AtRoot,
    RootPage,
    TargetUnavailable,
    PresentationFailed,
    BackPending,
    BackCancelled,
    BackTimeout,
    StaleRequest,
    DeclarationInUse,
    IdentityMismatch,
};

enum class BackDecision {
    Allow,
    Cancel,
    Defer,
};

enum class BackPresentation {
    Framework,
    AppOwned,
};

struct CardDeclaration {
    std::string card_id;
    std::string target_page_id;
};

struct PageDeclaration {
    std::string app_id;
    std::string root_page_id;
    std::vector<std::string> page_ids;
    std::vector<CardDeclaration> cards = {};
    BackPresentation back_presentation = BackPresentation::Framework;
    bool uses_standard_back_control = false;
};

std::expected<void, NavigationError> validate_page_declaration(const PageDeclaration &declaration);

struct PageSnapshot {
    std::string app_id;
    std::string page_id;
    bool can_back = false;
    bool back_pending = false;
};

class PageNavigator {
public:
    using Presenter = std::function<bool(std::string_view from, std::string_view to)>;
    using BackHandler = std::function<BackDecision(const PageSnapshot &, uint64_t token)>;
    using AvailabilityHandler = std::function<void(bool default_visible, bool edge_enabled)>;
    using DiagnosticHandler = std::function<void(NavigationError error, std::string_view target)>;
    static constexpr uint64_t BACK_TIMEOUT_MS = 15'000;

    static std::expected<PageNavigator, NavigationError> create(
        PageDeclaration declaration,
        Presenter presenter
    );

    std::expected<void, NavigationError> start();
    std::expected<void, NavigationError> start_from_card(std::string_view card_id);
    std::expected<void, NavigationError> push(std::string_view page_id);
    std::expected<void, NavigationError> pop();
    std::expected<void, NavigationError> replace(std::string_view page_id);
    std::expected<void, NavigationError> reset_to_root();
    std::expected<void, NavigationError> update_declaration(PageDeclaration declaration);
    void set_back_handler(BackHandler handler);
    void set_availability_handler(AvailabilityHandler handler);
    void set_diagnostic_handler(DiagnosticHandler handler);
    std::expected<std::optional<uint64_t>, NavigationError> request_back(uint64_t now_ms);
    std::expected<void, NavigationError> complete_back(uint64_t token, bool allow);
    std::optional<NavigationError> expire_back(uint64_t now_ms);
    void stop();
    PageSnapshot snapshot() const;
    bool show_default_back() const;
    bool edge_back_enabled() const;
    bool framework_owns_back() const;

private:
    PageNavigator(PageDeclaration declaration, Presenter presenter);
    bool declares(std::string_view page_id) const;
    std::expected<void, NavigationError> present(std::string_view to);
    void publish_availability() const;

    PageDeclaration declaration_;
    Presenter presenter_;
    BackHandler back_handler_;
    AvailabilityHandler availability_handler_;
    DiagnosticHandler diagnostic_handler_;
    std::vector<std::string> stack_;
    struct PendingBack {
        uint64_t token;
        uint64_t started_ms;
    };
    std::optional<PendingBack> pending_back_;
    uint64_t next_back_token_ = 1;
    mutable std::unique_ptr<std::recursive_mutex> mutex_ =
        std::make_unique<std::recursive_mutex>();
};

} // namespace espocket
