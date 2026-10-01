#pragma once

#include <cstdint>
#include <expected>
#include <functional>
#include <mutex>
#include <string>

namespace espocket {

class TestInputQueue {
public:
    static constexpr uint64_t TIMEOUT_MS = 1'000;
    std::expected<void, std::string> enqueue(uint64_t now_ms, uint64_t context_token = 0);
    bool execute_pending(const std::function<void()> &execute);
    bool execute_pending_context(const std::function<void(uint64_t)> &execute);
    bool expire(uint64_t now_ms);
    void cancel_pending();
    bool busy() const;
    std::expected<void, std::string> reserve_touch();
    void finish_touch();

private:
    enum class State { Idle, Pending, Executing, Touch };
    void finish();
    mutable std::mutex mutex_;
    State state_ = State::Idle;
    uint64_t queued_ms_ = 0;
    uint64_t context_token_ = 0;
};

} // namespace espocket
