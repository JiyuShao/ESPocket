#pragma once

#include <cstddef>
#include <cstdint>
#include <expected>
#include <functional>
#include <string>
#include <vector>

#include "espocket/test_input_queue.hpp"

namespace espocket {

struct TouchInputStep {
    int32_t x = 0;
    int32_t y = 0;
    uint32_t elapsed_ms = 0;
    bool pressed = true;
};

// Called by one input worker. The shared queue arbitrates against System PWR.
// Sink sends raw input; cleanup must remove the override before releasing the slot.
class TouchInputSequence {
public:
    using Sink = std::function<std::expected<void, std::string>(const TouchInputStep &, bool first)>;
    using Cleanup = std::function<std::expected<void, std::string>(bool cancelled)>;
    static constexpr uint32_t MIN_STEP_MS = 40;
    static constexpr uint32_t MAX_DURATION_MS = 2'000;
    static constexpr uint32_t DEADLINE_GRACE_MS = 500;

    TouchInputSequence(TestInputQueue &queue, Sink sink, Cleanup cleanup);
    std::expected<void, std::string> start(std::vector<TouchInputStep> steps,
                                         int32_t width, int32_t height, uint64_t now_ms);
    std::expected<void, std::string> tick(uint64_t now_ms);
    std::expected<void, std::string> cancel();
    bool active() const;

private:
    std::expected<void, std::string> clean();
    TestInputQueue &queue_;
    Sink sink_;
    Cleanup cleanup_;
    std::vector<TouchInputStep> steps_;
    size_t next_ = 0;
    uint64_t started_ms_ = 0;
    uint64_t delivered_ms_ = 0;
    bool active_ = false;
    bool cleaning_ = false;
    bool cancelled_ = false;
};

} // namespace espocket
