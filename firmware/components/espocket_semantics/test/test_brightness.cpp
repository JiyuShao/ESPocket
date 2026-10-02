#include "espocket/brightness.hpp"
#include <cassert>
#include <cmath>
using namespace espocket::semantic;
int main() {
    double actual = 40;
    int reads = 0, writes = 0, admissions = 0;
    bool grant = false, read_failure = false, write_failure = false, revoke = false, clamp = false;
    const Caller ui{CallerKind::ProductUi, "shell", 0};
    const Caller assistant{CallerKind::Assistant, "assistant", 0};
    Brightness brightness("panel.selected",
        [&]() -> std::expected<double, std::string> {
            ++reads;
            if (read_failure) return std::unexpected("read_timeout");
            return actual;
        },
        [&](double requested) -> std::expected<void, std::string> {
            ++writes;
            actual = clamp ? requested - 1 : requested;
            if (write_failure) return std::unexpected("write_timeout");
            return {};
        },
        [&](const Access& access) {
            assert(access.target_id == "panel.selected");
            assert(access.capability_id == "display.brightness");
            ++admissions;
            bool authorized = access.caller.kind == CallerKind::ProductUi || grant;
            if (revoke && admissions > 1) authorized = false;
            return Permission{authorized, true, true};
        });
    assert(valid_registration(brightness.discovery()));
    assert(!brightness.read(assistant));
    assert(brightness.set(assistant, 60).status == ResultStatus::NotExecuted);
    assert(reads == 0 && writes == 0);
    assert(brightness.read(ui)->percent == 40);
    grant = true;
    auto set = brightness.set(assistant, 60);
    assert(set.status == ResultStatus::Succeeded && set.observed->percent == 60);
    assert(set.event && set.event->previous == 40 && set.event->caller.id == "assistant");
    set = brightness.set(ui, 60);
    assert(set.status == ResultStatus::Succeeded && !set.event);
    clamp = true;
    set = brightness.set(ui, 80);
    assert(set.observed->percent == 79 && set.event->observed == 79);
    clamp = false;
    const int before = writes;
    assert(brightness.set(ui, 120).status == ResultStatus::NotExecuted);
    assert(brightness.set(ui, NAN).status == ResultStatus::NotExecuted);
    assert(brightness.set(ui, 20, [] { return true; }).status == ResultStatus::Cancelled);
    int cancellations = 0;
    assert(brightness.set(ui, 20, [&] { return ++cancellations > 1; }).status == ResultStatus::Cancelled);
    admissions = 0; revoke = true;
    assert(brightness.set(ui, 20).status == ResultStatus::NotExecuted);
    assert(writes == before);
    revoke = false; read_failure = true;
    assert(brightness.set(ui, 20).status == ResultStatus::Failed);
    assert(writes == before);
    read_failure = false; write_failure = true;
    set = brightness.set(ui, 20);
    assert(set.status == ResultStatus::Uncertain && !set.observed && !set.event);
    assert(actual == 20 && writes == before + 1); // no blind retry / pretend rollback
    write_failure = false;
    Brightness observation_failure("panel.selected", [&]() -> std::expected<double, std::string> {
        if (writes > before + 1) return std::unexpected("post_submit_failure");
        return actual;
    }, [&](double requested) -> std::expected<void, std::string> { ++writes; actual = requested; return {}; },
    [](const Access&) { return Permission{true, true, true}; });
    set = observation_failure.set(ui, 90);
    assert(set.status == ResultStatus::Uncertain && !set.event && writes == before + 2);
    auto handle = brightness.handle();
    brightness.invalidate();
    assert(!handle.valid() && !brightness.read(ui));
    assert(brightness.set(ui, 20).status == ResultStatus::NotExecuted);
    assert(writes == before + 2);
}
