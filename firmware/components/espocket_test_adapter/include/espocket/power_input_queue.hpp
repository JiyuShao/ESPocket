#pragma once

#include <cstdint>
#include <expected>
#include <functional>
#include <mutex>
#include <string>

namespace espocket {

class PowerInputQueue {
public:
    static constexpr uint64_t TIMEOUT_MS = 1'000;
    std::expected<void, std::string> enqueue(uint64_t now_ms);
    bool execute_pending(const std::function<void()> &execute);
    bool expire(uint64_t now_ms);
    void cancel_pending();
    bool busy() const;

private:
    enum class State { Idle, Pending, Executing };
    void finish();
    mutable std::mutex mutex_;
    State state_ = State::Idle;
    uint64_t queued_ms_ = 0;
};

} // namespace espocket
