#pragma once
#include "espocket/water_simulation.hpp"
#include <condition_variable>
#include <expected>
#include <mutex>
#include <optional>
#include <string>
#include <thread>
namespace espocket::water {
// One App-owned worker, two bounded image slots and one coalesced pending update.
// No GUI or AppContext access occurs on the worker.
class Worker {
public:
    enum class Status { Stopped, Starting, Ready, Failed };
    Worker() = default;
    ~Worker();
    Worker(const Worker &) = delete;
    Worker &operator=(const Worker &) = delete;
    std::expected<void, std::string> start();
    std::expected<void, std::string> pause();
    std::expected<void, std::string> resume();
    std::expected<void, std::string> stop();
    void submit(uint64_t now_ms, Impulse);
    void cancel_input();
    std::shared_ptr<const Frame> take_frame();
    Status status() const;
private:
    void run() noexcept;
    void request_stop();
    struct Update { uint64_t now_ms = 0; Impulse touch; };
    mutable std::mutex mutex_;
    std::condition_variable wake_, settled_;
    std::thread thread_;
    std::atomic_bool cancelled_{false};
    bool paused_ = false, stopping_ = false, busy_ = false;
    uint64_t generation_ = 0;
    Status status_ = Status::Stopped;
    std::optional<Update> pending_;
    std::shared_ptr<const Frame> latest_;
};
}
