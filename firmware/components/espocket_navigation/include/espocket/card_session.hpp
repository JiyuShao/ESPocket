#pragma once

#include <expected>
#include <functional>
#include <memory>
#include <optional>

#include "espocket/card_registry.hpp"

namespace espocket {

// Implemented by the App binding. All calls run synchronously on the GUI owner task.
// Destruction releases the UI and subscriptions; pause stops visible-only work.
class CardContent {
public:
    virtual ~CardContent() = default;
    virtual bool show() noexcept = 0;
    virtual bool refresh() noexcept = 0;
    virtual void pause() noexcept = 0;
    virtual bool action(std::string_view) noexcept { return false; }
};

enum class CardVisibility { Empty, Paused, Visible };
enum class CardSessionError {
    Busy, DeclarationUnavailable, NotConfigured, CreationFailed,
    PresentationFailed, RefreshFailed, NoCard, LaunchFailed,
};

// One Home Space presentation slot, not a Core App instance or a Page stack.
// Serialize calls with registry updates on the GUI owner task. Callbacks must not throw
// or modify the registry. Reentrant session operations return Busy.
class CardSession {
public:
    using Factory = std::function<std::unique_ptr<CardContent>(const CardKey &)>;
    using AppLauncher = std::function<bool(const CardKey &, std::string_view target_page)>;
    CardSession(CardRegistry &registry, Factory factory);
    ~CardSession();
    CardSession(const CardSession &) = delete;
    CardSession &operator=(const CardSession &) = delete;

    std::expected<void, CardSessionError> show(const CardKey &key);
    std::expected<void, CardSessionError> pause();
    std::expected<void, CardSessionError> release();
    // Registry removal notifications are forwarded here by the composition owner.
    std::expected<void, CardSessionError> invalidate(const CardKey &key);
    std::expected<void, CardSessionError> open_app(const AppLauncher &launcher);
    std::expected<void, CardSessionError> action(std::string_view action);
    CardVisibility visibility() const { return visibility_; }
    bool busy() const { return busy_; }
    std::optional<CardKey> key() const { return key_; }

private:
    void pause_content();
    void release_content();
    CardRegistry &registry_;
    Factory factory_;
    std::unique_ptr<CardContent> content_;
    std::optional<CardKey> key_;
    CardVisibility visibility_ = CardVisibility::Empty;
    bool busy_ = false;
};

} // namespace espocket
