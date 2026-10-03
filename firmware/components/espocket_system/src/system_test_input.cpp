#include "system_internal.hpp"

namespace espocket {

std::expected<void, std::string> System::start_test_touch(std::vector<TouchInputStep> steps)
{
    if (stopping_.load(std::memory_order_acquire) || !test_touch_input_ || !shell_ ||
            !developer_mode_->enabled() || !display_on_.load(std::memory_order_acquire)) {
        return std::unexpected("invalid_state");
    }
    auto result = test_touch_input_->start(std::move(steps), static_cast<int32_t>(display_width_),
                                          static_cast<int32_t>(display_height_),
                                          static_cast<uint64_t>(esp_timer_get_time() / 1000));
    if (result) {
        test_touch_foreground_token_ = foreground_token_->load(std::memory_order_acquire);
        cancel_test_touch_.store(false, std::memory_order_release);
    }
    return result;
}

std::expected<void, std::string> System::tick_test_touch()
{
    if (!test_touch_input_ || !test_touch_input_->active()) { return {}; }
    if (stopping_.load(std::memory_order_acquire) || !developer_mode_->enabled() ||
            !display_on_.load(std::memory_order_acquire) ||
            cancel_test_touch_.exchange(false, std::memory_order_acq_rel) ||
            (foreground_token_->load(std::memory_order_acquire) != test_touch_foreground_token_ &&
             !test_touch_input_->release_delivered())) {
        return test_touch_input_->cancel();
    }
    // A delivered release can launch an App. No points remain to cross into
    // the new task, so keep normal cleanup rather than manufacturing cancel.
    return test_touch_input_->tick(static_cast<uint64_t>(esp_timer_get_time() / 1000));
}

std::expected<void, std::string> System::release_test_input()
{
    if (test_power_input_) { test_power_input_->cancel_pending(); }
    return test_touch_input_ ? test_touch_input_->cancel() : std::expected<void, std::string>{};
}

} // namespace espocket
