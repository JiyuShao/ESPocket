#include "espocket/touch_input_sequence.hpp"

#include <utility>

namespace espocket {

TouchInputSequence::TouchInputSequence(TestInputQueue &queue, Sink sink, Cleanup cleanup)
    : queue_(queue), sink_(std::move(sink)), cleanup_(std::move(cleanup))
{}

std::expected<void, std::string> TouchInputSequence::start(
    std::vector<TouchInputStep> steps, int32_t width, int32_t height, uint64_t now_ms)
{
    if (active_) { return std::unexpected("busy"); }
    if (!sink_ || !cleanup_) { return std::unexpected("invalid_state"); }
    if (width <= 0 || height <= 0 || steps.size() < 2 || steps.size() > 16 ||
            steps.front().elapsed_ms != 0 || !steps.front().pressed ||
            steps.back().pressed || steps.back().elapsed_ms > MAX_DURATION_MS ||
            steps.back().x != steps[steps.size() - 2].x ||
            steps.back().y != steps[steps.size() - 2].y) {
        return std::unexpected("bad_request");
    }
    for (size_t i = 0; i < steps.size(); ++i) {
        const auto &step = steps[i];
        if (step.x < 0 || step.y < 0 || step.x >= width || step.y >= height ||
                (i + 1 < steps.size() && !step.pressed) ||
                (i > 0 && (step.elapsed_ms < steps[i - 1].elapsed_ms ||
                           step.elapsed_ms - steps[i - 1].elapsed_ms < MIN_STEP_MS))) {
            return std::unexpected("bad_request");
        }
    }
    auto reserved = queue_.reserve_touch();
    if (!reserved) { return reserved; }
    steps_ = std::move(steps);
    next_ = 0;
    started_ms_ = now_ms;
    delivered_ms_ = now_ms;
    active_ = true;
    cleaning_ = false;
    cancelled_ = false;
    return {};
}

std::expected<void, std::string> TouchInputSequence::tick(uint64_t now_ms)
{
    if (!active_) { return {}; }
    if (cleaning_) { return clean(); }
    if (now_ms < started_ms_ || now_ms < delivered_ms_ ||
            now_ms - started_ms_ > steps_.back().elapsed_ms + DEADLINE_GRACE_MS) {
        auto result = cancel();
        return result ? std::unexpected("timeout") : result;
    }
    if (next_ == steps_.size()) {
        if (now_ms - delivered_ms_ >= MIN_STEP_MS) {
            cleaning_ = true;
            return clean();
        }
        return {};
    }
    // Never catch up multiple points in one tick: LVGL must observe press and release separately.
    if (next_ > 0 && now_ms - delivered_ms_ <
            steps_[next_].elapsed_ms - steps_[next_ - 1].elapsed_ms) {
        return {};
    }
    auto sent = sink_(steps_[next_], next_ == 0);
    if (!sent) {
        auto cleaned = cancel();
        return cleaned ? sent : cleaned;
    }
    ++next_;
    delivered_ms_ = now_ms;
    return {};
}

std::expected<void, std::string> TouchInputSequence::cancel()
{
    if (!active_) { return {}; }
    cleaning_ = true;
    cancelled_ = true;
    return clean();
}

std::expected<void, std::string> TouchInputSequence::clean()
{
    auto result = cleanup_(cancelled_);
    if (!result) { return result; }
    steps_.clear();
    active_ = false;
    cleaning_ = false;
    queue_.finish_touch();
    return {};
}

bool TouchInputSequence::active() const { return active_; }

} // namespace espocket
