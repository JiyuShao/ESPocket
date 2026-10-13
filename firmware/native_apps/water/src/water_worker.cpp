#include "water_worker.hpp"
#include <algorithm>
#include <chrono>
#include <utility>
#ifdef ESP_PLATFORM
#include "esp_pthread.h"
#include "esp_heap_caps.h"
#endif
namespace espocket::water {
namespace { constexpr auto settle_timeout = std::chrono::milliseconds(1500); }
Worker::~Worker()
{
    request_stop();
    // The solver is bounded and observes cancellation between substeps. It never waits for GUI.
    if (thread_.joinable()) thread_.join();
}
std::expected<void, std::string> Worker::start()
{
    std::lock_guard lock(mutex_);
    if (thread_.joinable()) return std::unexpected("Water worker already started");
    paused_ = stopping_ = false; busy_ = true; cancelled_ = false;
    pending_.reset(); latest_.reset(); ++generation_; status_ = Status::Starting;
#ifdef ESP_PLATFORM
    auto previous = esp_pthread_get_default_config();
    esp_pthread_get_cfg(&previous);
    auto config = esp_pthread_get_default_config();
    config.stack_size = 6144; config.prio = 3; config.pin_to_core = 1; config.thread_name = "water";
    config.stack_alloc_caps = MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT;
    if (esp_pthread_set_cfg(&config) != ESP_OK) {
        busy_ = false; status_ = Status::Stopped;
        return std::unexpected("Water thread configuration failed");
    }
#endif
    try { thread_ = std::thread([this] { run(); }); }
    catch (const std::exception &) {
#ifdef ESP_PLATFORM
        esp_pthread_set_cfg(&previous);
#endif
        busy_ = false; status_ = Status::Stopped;
        return std::unexpected("Water worker creation failed");
    }
#ifdef ESP_PLATFORM
    esp_pthread_set_cfg(&previous);
#endif
    return {};
}
std::expected<void, std::string> Worker::pause()
{
    std::unique_lock lock(mutex_);
    paused_ = true; cancelled_ = true; ++generation_; pending_.reset(); latest_.reset();
    wake_.notify_all();
    if (!settled_.wait_for(lock, settle_timeout, [this] { return !busy_; }))
        return std::unexpected("Water pause has not settled");
    return {};
}
std::expected<void, std::string> Worker::resume()
{
    std::lock_guard lock(mutex_);
    if (busy_ || stopping_ || status_ == Status::Stopped)
        return std::unexpected("Water worker cannot resume");
    cancelled_ = false; paused_ = false; ++generation_; pending_.reset();
    wake_.notify_all();
    return {};
}
void Worker::request_stop()
{
    std::lock_guard lock(mutex_);
    stopping_ = true; cancelled_ = true; ++generation_; pending_.reset(); latest_.reset();
    wake_.notify_all();
}
std::expected<void, std::string> Worker::stop()
{
    request_stop();
    std::unique_lock lock(mutex_);
    if (!thread_.joinable()) { status_ = Status::Stopped; return {}; }
    if (!settled_.wait_for(lock, settle_timeout, [this] { return status_ == Status::Stopped; }))
        return std::unexpected("Water worker has not stopped; resources retained");
    lock.unlock(); thread_.join();
    return {};
}
void Worker::submit(uint64_t now_ms, Impulse touch)
{
    std::lock_guard lock(mutex_);
    if (paused_ || stopping_ || status_ == Status::Stopped || status_ == Status::Failed) return;
    if (pending_ && pending_->touch.active && touch.active) {
        touch.vx = std::clamp(touch.vx + pending_->touch.vx, -600.0f, 600.0f);
        touch.vy = std::clamp(touch.vy + pending_->touch.vy, -600.0f, 600.0f);
        touch.burst = std::max(touch.burst, pending_->touch.burst);
    } else if (pending_ && pending_->touch.active && !touch.active) {
        touch = pending_->touch;
    }
    pending_ = Update{now_ms, touch}; wake_.notify_one();
}
void Worker::cancel_input()
{
    std::lock_guard lock(mutex_);
    if (pending_) pending_->touch = {};
}
std::shared_ptr<const Frame> Worker::take_frame()
{
    std::lock_guard lock(mutex_);
    auto frame = std::exchange(latest_, {});
    wake_.notify_one();
    return frame;
}
Worker::Status Worker::status() const { std::lock_guard lock(mutex_); return status_; }
void Worker::run() noexcept
{
    try {
        Simulation simulation;
        std::array<std::shared_ptr<Frame>, 2> pool{Frame::create(), Frame::create()};
        const bool initialized = pool[0] && pool[1] && simulation.initialize();
        if (!initialized) pool = {};
        {
            std::lock_guard lock(mutex_);
            status_ = initialized ? Status::Ready : Status::Failed;
            busy_ = false; settled_.notify_all();
        }
        uint64_t last_ms = 0, last_generation = 0;
        for (;;) {
            std::unique_lock lock(mutex_);
            wake_.wait(lock, [this] { return stopping_ || (!paused_ && pending_.has_value()); });
            if (stopping_) break;
            if (!initialized) { pending_.reset(); continue; }
            std::shared_ptr<Frame> frame;
            for (const auto &slot : pool) if (slot.use_count() == 1) { frame = slot; break; }
            if (!frame) {
                // Keep the single coalesced update until a reader releases a slot.
                // Recheck on consumption/next timer; no spin and no discarded touch impulse.
                wake_.wait(lock);
                continue;
            }
            const auto update = *pending_; pending_.reset();
            const auto generation = generation_;
            const unsigned elapsed = generation == last_generation && last_ms && update.now_ms > last_ms
                ? static_cast<unsigned>(std::min<uint64_t>(100, update.now_ms - last_ms)) : 33;
            last_ms = update.now_ms; last_generation = generation; busy_ = true;
            lock.unlock();
            const bool painted = simulation.advance(elapsed, update.touch, *frame, cancelled_);
            lock.lock();
            if (painted && !paused_ && !stopping_ && generation == generation_) latest_ = std::move(frame);
            busy_ = false; settled_.notify_all();
        }
        // Solver and pool are destroyed before publishing Stopped.
    } catch (const std::exception &) {
        std::unique_lock lock(mutex_);
        status_ = Status::Failed; busy_ = false; settled_.notify_all();
        wake_.wait(lock, [this] { return stopping_; });
    }
    std::lock_guard lock(mutex_);
    busy_ = false; status_ = Status::Stopped; settled_.notify_all();
}
}
