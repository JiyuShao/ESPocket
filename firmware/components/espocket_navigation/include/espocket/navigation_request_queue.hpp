#pragma once

#include <deque>
#include <expected>
#include <functional>
#include <mutex>
#include <string>
#include <cstdint>

namespace espocket {

// Producers only enqueue; the serialized App owner consumes and performs effects.
class NavigationRequestQueue {
public:
    using Result = std::expected<std::string, std::string>;
    using Reply = std::function<void(Result)>;
    using Execute = std::function<Result(uint32_t app, std::string_view request)>;
    static constexpr size_t CAPACITY = 16;
    static constexpr uint64_t TIMEOUT_MS = 2'000;
    void enqueue(uint32_t app, uint64_t generation, uint64_t now, std::string request, Reply reply);
    void drain(uint32_t foreground_app, uint64_t generation, uint64_t now, const Execute &execute);
    void close();

private:
    struct Request { uint32_t app; uint64_t generation; uint64_t submitted; std::string json; Reply reply; };
    std::mutex mutex_;
    std::deque<Request> pending_;
    bool closed_ = false;
};
} // namespace espocket
