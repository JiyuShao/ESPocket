#pragma once

#include <atomic>
#include <cstdint>
#include <memory>
#include <string>

namespace espocket::semantic {

enum class OwnerKind { System, Shell, Service, App };
enum class Lifetime { Owner, RunningInstance };
enum class Operation { ReadContext, ExecuteAction, ObserveEvent };
enum class ActionRisk { ReadOnly, Reversible, HighImpact };
enum class CancellationBoundary { BeforeSubmission };
enum class ResultStatus { Succeeded, NotExecuted, Failed, Cancelled, Uncertain };
enum class CallerKind { ProductUi, Assistant, App };

struct Caller {
    CallerKind kind;
    std::string id;
    uint64_t running_instance = 0;
};

struct OwnerIdentity {
    OwnerKind kind;
    std::string id;
    uint64_t running_instance = 0;
};

// Discovery describes a capability. It never carries authority or live state.
struct Registration {
    std::string capability_id;
    OwnerIdentity owner;
    Lifetime lifetime;
    std::string context_id;
    std::string action_id;
    std::string event_id;
    ActionRisk risk;
    CancellationBoundary cancellation = CancellationBoundary::BeforeSubmission;
};

// Evaluated by the trusted admission implementation for each concrete access.
// These are conclusions, not caller-supplied proof or a persisted grant store.
struct Permission {
    bool product_authorized = false;
    bool owner_admitted = false;
    bool framework_admitted = false;
    bool allows() const { return product_authorized && owner_admitted && framework_admitted; }
};

struct Access {
    Caller caller;
    Operation operation;
    std::string capability_id;
    std::string target_id;
    ActionRisk risk;
};

// A handle owns no capability implementation. Destruction/invalidation by the
// actual Owner revokes every copy; restarting an App requires a new LifetimeScope.
class LifetimeScope {
    struct State { std::atomic<bool> active{true}; };
public:
    class Handle {
    public:
        bool valid() const {
            const auto state = state_.lock();
            return state && state->active.load(std::memory_order_acquire);
        }
    private:
        friend class LifetimeScope;
        explicit Handle(const std::shared_ptr<State>& state) : state_(state) {}
        std::weak_ptr<State> state_;
    };
    LifetimeScope() = default;
    LifetimeScope(const LifetimeScope&) = delete;
    LifetimeScope& operator=(const LifetimeScope&) = delete;
    ~LifetimeScope() { invalidate(); }
    Handle handle() const { return Handle(state_); }
    void invalidate() { state_->active.store(false, std::memory_order_release); }
private:
    std::shared_ptr<State> state_ = std::make_shared<State>();
};

inline bool valid_registration(const Registration& value)
{
    if (value.capability_id.empty() || value.owner.id.empty() ||
        (value.context_id.empty() && value.action_id.empty() && value.event_id.empty())) return false;
    if (value.owner.kind == OwnerKind::App)
        return value.lifetime == Lifetime::RunningInstance && value.owner.running_instance != 0;
    return value.lifetime == Lifetime::Owner && value.owner.running_instance == 0;
}

} // namespace espocket::semantic
