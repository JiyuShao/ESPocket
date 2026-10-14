#pragma once
#include "espocket/orbit_renderer.hpp"
#include <condition_variable>
#include <expected>
#include <mutex>
#include <optional>
#include <string>
#include <thread>
namespace espocket::orbit {
// One App-owned worker, two bounded image slots and one coalesced pending update.
// No GUI or AppContext access occurs on the worker.
class Worker {
public:
    enum class Status { Stopped, Starting, Ready, Failed };
    Worker() = default;
    ~Worker();
    Worker(const Worker &) = delete;
    Worker &operator=(const Worker &) = delete;
    std::expected<void, std::string> start(Kind);
    std::expected<void, std::string> pause();
    std::expected<void, std::string> resume();
    std::expected<void, std::string> stop();
    void submit(Attitude);
    std::shared_ptr<const Frame> take_frame();
    Status status() const;
private:
    void run() noexcept;
    void request_stop();
    Kind kind_ = Kind::Moon;
    mutable std::mutex mutex_;
    std::condition_variable wake_, settled_;
    std::thread thread_;
    std::atomic_bool cancelled_{false};
    bool paused_ = false, stopping_ = false, busy_ = false;
    uint64_t generation_ = 0;
    Status status_ = Status::Stopped;
    std::optional<Attitude> pending_;
    std::shared_ptr<const Frame> latest_;
};
}
