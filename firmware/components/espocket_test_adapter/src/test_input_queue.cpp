#include "espocket/test_input_queue.hpp"

namespace espocket {

std::expected<void, std::string> TestInputQueue::enqueue(uint64_t now_ms)
{
    std::lock_guard lock(mutex_);
    if (state_ != State::Idle) {
        return std::unexpected("busy");
    }
    state_ = State::Pending;
    queued_ms_ = now_ms;
    return {};
}

bool TestInputQueue::execute_pending(const std::function<void()> &execute)
{
    {
        std::lock_guard lock(mutex_);
        if (state_ != State::Pending) {
            return false;
        }
        state_ = State::Executing;
    }
    struct Completion {
        TestInputQueue &queue;
        ~Completion() { queue.finish(); }
    } completion{*this};
    execute();
    return true;
}

void TestInputQueue::finish()
{
    std::lock_guard lock(mutex_);
    state_ = State::Idle;
}

bool TestInputQueue::expire(uint64_t now_ms)
{
    std::lock_guard lock(mutex_);
    if (state_ != State::Pending || now_ms < queued_ms_ || now_ms - queued_ms_ < TIMEOUT_MS) {
        return false;
    }
    state_ = State::Idle;
    return true;
}

void TestInputQueue::cancel_pending()
{
    std::lock_guard lock(mutex_);
    if (state_ == State::Pending) {
        state_ = State::Idle;
    }
}

bool TestInputQueue::busy() const
{
    std::lock_guard lock(mutex_);
    return state_ != State::Idle;
}

std::expected<void, std::string> TestInputQueue::reserve_touch()
{
    std::lock_guard lock(mutex_);
    if (state_ != State::Idle) { return std::unexpected("busy"); }
    state_ = State::Touch;
    return {};
}

void TestInputQueue::finish_touch()
{
    std::lock_guard lock(mutex_);
    if (state_ == State::Touch) { state_ = State::Idle; }
}

} // namespace espocket
