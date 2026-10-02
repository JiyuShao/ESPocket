#include "espocket/navigation_request_queue.hpp"

namespace espocket {
void NavigationRequestQueue::enqueue(uint32_t app, uint64_t generation, uint64_t now,
                                      std::string request, Reply reply)
{
    std::string error;
    {
        std::lock_guard lock(mutex_);
        if (closed_) error = "system_unavailable";
        else if (generation == 0) error = "not_started";
        else if (request.size() > 4096) error = "bad_request";
        else if (pending_.size() >= CAPACITY) error = "busy";
        else { pending_.push_back({app, generation, now, std::move(request), std::move(reply)}); return; }
    }
    reply(std::unexpected(std::move(error)));
}

void NavigationRequestQueue::drain(uint32_t app, uint64_t generation, uint64_t now, const Execute &execute)
{
    std::deque<Request> work;
    { std::lock_guard lock(mutex_); work.swap(pending_); }
    for (auto &request : work) {
        if (request.app != app || request.generation != generation || generation == 0) {
            request.reply(std::unexpected("stale_request"));
        } else if (now < request.submitted || now - request.submitted >= TIMEOUT_MS) {
            request.reply(std::unexpected("timeout"));
        } else {
            request.reply(execute(request.app, request.json));
        }
    }
}

void NavigationRequestQueue::close()
{
    std::deque<Request> work;
    { std::lock_guard lock(mutex_); closed_ = true; work.swap(pending_); }
    for (auto &request : work) request.reply(std::unexpected("system_unavailable"));
}
} // namespace espocket
