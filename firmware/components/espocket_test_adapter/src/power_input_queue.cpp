#include "espocket/power_input_queue.hpp"

namespace espocket {

std::expected<void, std::string> PowerInputQueue::enqueue(uint64_t now_ms)
{
    std::lock_guard lock(mutex_);
    if (state_ != State::Idle) {
        return std::unexpected("busy");
    }
    state_ = State::Pending;
    queued_ms_ = now_ms;
    return {};
}

bool PowerInputQueue::execute_pending(const std::function<void()> &execute)
{
    {
        std::lock_guard lock(mutex_);
        if (state_ != State::Pending) {
            return false;
        }
        state_ = State::Executing;
    }
    struct Completion {
        PowerInputQueue &queue;
        ~Completion() { queue.finish(); }
    } completion{*this};
    execute();
    return true;
}

void PowerInputQueue::finish()
{
    std::lock_guard lock(mutex_);
    state_ = State::Idle;
}

bool PowerInputQueue::expire(uint64_t now_ms)
{
    std::lock_guard lock(mutex_);
    if (state_ != State::Pending || now_ms < queued_ms_ || now_ms - queued_ms_ < TIMEOUT_MS) {
        return false;
    }
    state_ = State::Idle;
    return true;
}

void PowerInputQueue::cancel_pending()
{
    std::lock_guard lock(mutex_);
    if (state_ == State::Pending) {
        state_ = State::Idle;
    }
}

bool PowerInputQueue::busy() const
{
    std::lock_guard lock(mutex_);
    return state_ != State::Idle;
}

} // namespace espocket
