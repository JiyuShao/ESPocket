#include <cstdlib>
#include <iostream>
#include <string_view>
#include <future>
#include <algorithm>

#include "espocket/developer_mode.hpp"
#include "espocket/test_protocol.hpp"
#include "espocket/power_input_queue.hpp"

void require(bool condition, std::string_view message)
{
    if (!condition) {
        std::cerr << message << '\n';
        std::exit(1);
    }
}

int main()
{
    bool stored = false;
    espocket::DeveloperMode mode(
        [&]() -> std::expected<bool, std::string> { return stored; },
        [&](bool value) -> std::expected<void, std::string> {
            stored = value;
            return {};
        }
    );
    require(mode.restore().has_value() && !mode.enabled(), "developer mode defaults off");
    espocket::TestProtocol protocol(mode, "image-123");
    require(protocol.dispatch(1, "hello").error_code == "developer_mode_off",
            "disabled developer mode rejects USB test commands");
    require(mode.set_enabled(true).has_value() && stored, "enabling persists before exposure");
    auto hello = protocol.dispatch(1, "hello");
    require(hello.ok && hello.image_identity == "image-123" &&
                hello.capabilities.size() == 1 && hello.capabilities[0] == "hello",
            "hello reports the image and only implemented capability");
    require(protocol.dispatch(2, "hello").error_code == "bad_request",
            "unknown protocol version is rejected");
    require(protocol.dispatch(1, "stimulus.touch").error_code == "unsupported",
            "unimplemented stimulus cannot modify product state");
    require(mode.set_enabled(false).has_value() && !stored &&
                protocol.dispatch(1, "hello").error_code == "developer_mode_off",
            "disabling closes the adapter without a reboot");

    auto restored = espocket::DeveloperMode(
        [&]() -> std::expected<bool, std::string> { return stored; },
        [&](bool value) -> std::expected<void, std::string> {
            stored = value;
            return {};
        }
    );
    require(restored.restore().has_value() && !restored.enabled(),
            "persisted disabled state survives a new instance");

    int snapshot_reads = 0;
    bool snapshot_failure = false;
    espocket::TestSnapshot owner_state{
        .surface = "launcher", .display = true, .foreground_app_id = "app.native",
        .page_id = "detail", .can_back = true,
    };
    espocket::TestProtocol observed(mode, "image-snapshot", [&]()
        -> std::expected<espocket::TestSnapshot, std::string> {
        ++snapshot_reads;
        if (snapshot_failure) { return std::unexpected("owner_unavailable"); }
        return owner_state;
    });
    require(observed.dispatch(1, "snapshot").error_code == "developer_mode_off" &&
                snapshot_reads == 0,
            "disabled snapshots must not read Owner state");
    require(mode.set_enabled(true).has_value(), "snapshot fixture should enable the gate");
    auto observed_hello = observed.dispatch(1, "hello");
    require(observed_hello.ok && std::ranges::find(observed_hello.capabilities, "snapshot") !=
                observed_hello.capabilities.end(),
            "hello should advertise snapshot only when an Owner reader is connected");
    auto first = observed.dispatch(1, "snapshot");
    require(first.ok && first.snapshot && first.snapshot->seq == 1 &&
                first.snapshot->page_id == "detail" && first.snapshot->can_back,
            "snapshot should expose the Owner's declared page and sequence");
    owner_state.page_id = "root";
    owner_state.can_back = false;
    auto second = observed.dispatch(1, "snapshot");
    require(second.ok && second.snapshot->seq > first.snapshot->seq &&
                second.snapshot->page_id == "root" && !second.snapshot->can_back,
            "successive snapshots must read current Owner state rather than cached navigation");
    snapshot_failure = true;
    auto failed_snapshot = observed.dispatch(1, "snapshot");
    require(!failed_snapshot.ok && failed_snapshot.error_code == "invalid_state" &&
                !failed_snapshot.snapshot,
            "unavailable Owner must not report fabricated Root state");
    snapshot_failure = false;
    auto after_failure = observed.dispatch(1, "snapshot");
    require(after_failure.ok && after_failure.snapshot->seq == second.snapshot->seq + 1,
            "failed reads must not publish a successful sample sequence");

    std::promise<void> entered;
    std::promise<void> release;
    auto released = release.get_future();
    espocket::TestProtocol slow(mode, "image-slow", [&]()
        -> std::expected<espocket::TestSnapshot, std::string> {
        entered.set_value();
        released.wait();
        return owner_state;
    });
    auto reading = std::async(std::launch::async, [&] { return slow.dispatch(1, "snapshot"); });
    entered.get_future().wait();
    require(slow.dispatch(1, "snapshot").error_code == "busy",
            "concurrent dispatch must be rejected without entering the Owner again");
    release.set_value();
    require(reading.get().ok, "original snapshot must complete after concurrent rejection");

    espocket::PowerInputQueue power;
    uint64_t now_ms = 10;
    int executions = 0;
    espocket::TestProtocol stimulated(mode, "image-power", [&]()
        -> std::expected<espocket::TestSnapshot, std::string> {
        return espocket::TestSnapshot{.input_busy = power.busy()};
    }, [&] { return power.enqueue(now_ms); }, [&]() -> std::expected<void, std::string> {
        power.cancel_pending();
        return {};
    });
    require(stimulated.dispatch(1, "stimulus.powerShort").ok && power.busy() && executions == 0,
            "USB stimulus should queue without executing the Owner on the transport thread");
    require(stimulated.dispatch(1, "stimulus.powerShort").error_code == "busy" &&
                stimulated.dispatch(1, "snapshot").snapshot->input_busy,
            "queued stimulus must reject another sequence and remain observable");
    require(stimulated.dispatch(1, "release").ok && stimulated.dispatch(1, "release").ok &&
                !power.busy() && !power.execute_pending([&] { ++executions; }),
            "release should idempotently cancel a pending stimulus without executing it");
    require(stimulated.dispatch(1, "stimulus.powerShort").ok &&
                !power.expire(now_ms + espocket::PowerInputQueue::TIMEOUT_MS - 1),
            "pending input should remain available before its deadline");
    require(power.expire(now_ms + espocket::PowerInputQueue::TIMEOUT_MS) && !power.busy() &&
                !power.execute_pending([&] { ++executions; }),
            "expired stimulus must not execute late");
    require(stimulated.dispatch(1, "stimulus.powerShort").ok &&
                power.execute_pending([&] { ++executions; }) && executions == 1 && !power.busy(),
            "Owner should consume exactly one queued PWR and free its slot");

    std::promise<void> power_entered;
    std::promise<void> power_release;
    auto power_released = power_release.get_future();
    require(stimulated.dispatch(1, "stimulus.powerShort").ok, "concurrent fixture should queue");
    auto executing = std::async(std::launch::async, [&] {
        return power.execute_pending([&] {
            power_entered.set_value();
            power_released.wait();
            ++executions;
        });
    });
    power_entered.get_future().wait();
    require(stimulated.dispatch(1, "release").ok && power.busy() &&
                stimulated.dispatch(1, "stimulus.powerShort").error_code == "busy",
            "release must not admit overlapping input while an Owner command is executing");
    power_release.set_value();
    require(executing.get() && !power.busy() && executions == 2,
            "already executing input finishes once and releases its slot");
    require(mode.set_enabled(false).has_value() &&
                stimulated.dispatch(1, "stimulus.powerShort").error_code == "developer_mode_off" &&
                !power.busy(),
            "disabled gate must prevent input from entering the queue");
}
