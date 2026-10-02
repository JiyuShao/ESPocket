#include "espocket/brightness.hpp"
#include <cmath>
#include <utility>
namespace espocket::semantic {
Brightness::Brightness(std::string target, Read read, Write write, Admission admission)
    : target_(std::move(target)), read_(std::move(read)), write_(std::move(write)),
      admission_(std::move(admission)),
      registration_{"display.brightness", {OwnerKind::Service, "brookesia.display", 0},
                    Lifetime::Owner, "display.brightness.context", "display.brightness.set",
                    "display.brightness.changed", ActionRisk::Reversible}
{}
void Brightness::invalidate() {
    std::lock_guard lock(mutex_);
    lifetime_.invalidate();
}
bool Brightness::allowed(const Caller& caller, Operation operation) const {
    return lifetime_.handle().valid() && !target_.empty() && !caller.id.empty() &&
        admission_ && admission_(Access{caller, operation, registration_.capability_id, target_,
            operation == Operation::ExecuteAction ? ActionRisk::Reversible : ActionRisk::ReadOnly}).allows();
}
std::expected<double, std::string> Brightness::observe() {
    if (!read_) return std::unexpected("owner_unavailable");
    auto value = read_();
    if (!value) return value;
    if (!std::isfinite(*value) || *value < 0 || *value > 100)
        return std::unexpected("invalid_owner_observation");
    return value;
}
std::expected<BrightnessContext, std::string> Brightness::read(const Caller& caller) {
    std::lock_guard lock(mutex_);
    if (!allowed(caller, Operation::ReadContext)) return std::unexpected("denied");
    auto value = observe();
    if (!value) return std::unexpected(value.error());
    return BrightnessContext{*value};
}
BrightnessResult Brightness::set(const Caller& caller, double percent, std::function<bool()> cancelled) {
    std::lock_guard lock(mutex_);
    if (!std::isfinite(percent) || percent < 0 || percent > 100)
        return {ResultStatus::NotExecuted, {}, {}, "invalid_percent"};
    if (!allowed(caller, Operation::ExecuteAction))
        return {ResultStatus::NotExecuted, {}, {}, "denied"};
    if (cancelled && cancelled()) return {ResultStatus::Cancelled, {}, {}, "before_submission"};
    auto before = observe();
    if (!before) return {ResultStatus::Failed, {}, {}, before.error()};
    // Re-evaluate authority immediately before the side effect.
    if (!allowed(caller, Operation::ExecuteAction))
        return {ResultStatus::NotExecuted, BrightnessContext{*before}, {}, "denied"};
    if (cancelled && cancelled())
        return {ResultStatus::Cancelled, BrightnessContext{*before}, {}, "before_submission"};
    if (!write_) return {ResultStatus::Failed, BrightnessContext{*before}, {}, "owner_unavailable"};
    auto written = write_(percent);
    // A failed service call may have timed out after applying the change. Never
    // report rollback/cancellation or retry. An acknowledged write still needs observation.
    if (!written) return {ResultStatus::Uncertain, {}, {}, written.error()};
    auto after = observe();
    if (!after) return {ResultStatus::Uncertain, {}, {}, after.error()};
    std::optional<BrightnessChanged> event;
    if (*after != *before && allowed(caller, Operation::ObserveEvent))
        event = BrightnessChanged{target_, *before, *after, caller};
    return {ResultStatus::Succeeded, BrightnessContext{*after}, std::move(event), {}};
}
} // namespace espocket::semantic
