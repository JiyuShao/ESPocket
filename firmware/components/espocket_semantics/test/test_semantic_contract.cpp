#include "espocket/semantic_contract.hpp"
#include <cassert>
#include <optional>
using namespace espocket::semantic;
int main() {
    Registration app{"notes.summary", {OwnerKind::App, "notes", 42}, Lifetime::RunningInstance,
                     "notes.context", "notes.open", "notes.changed", ActionRisk::Reversible};
    assert(valid_registration(app));
    app.owner.running_instance = 0;
    assert(!valid_registration(app));
    app.owner.running_instance = 42;
    app.lifetime = Lifetime::Owner;
    assert(!valid_registration(app));
    app.owner = {OwnerKind::Service, "display", 0};
    assert(valid_registration(app));
    app.action_id.clear();
    app.event_id.clear();
    assert(valid_registration(app)); // a Context-only capability is valid
    app.context_id.clear();
    assert(!valid_registration(app));
    app.capability_id.clear();
    assert(!valid_registration(app));
    for (int bits = 0; bits < 8; ++bits) {
        Permission permission{bool(bits & 1), bool(bits & 2), bool(bits & 4)};
        assert(permission.allows() == (bits == 7));
    }
    std::optional<LifetimeScope::Handle> stale;
    {
        LifetimeScope scope;
        stale = scope.handle();
        auto copy = *stale;
        assert(copy.valid());
        scope.invalidate();
        assert(!copy.valid() && !stale->valid());
    }
    LifetimeScope restarted;
    assert(restarted.handle().valid() && !stale->valid());
    {
        LifetimeScope stopped;
        stale = stopped.handle();
        assert(stale->valid());
    }
    assert(!stale->valid());
}
