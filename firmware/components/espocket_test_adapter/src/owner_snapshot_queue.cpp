#include "espocket/owner_snapshot_queue.hpp"

#include <utility>

namespace espocket {

OwnerSnapshotQueue::OwnerSnapshotQueue(TestProtocol::SnapshotReader reader)
    : reader_(std::move(reader)) {}

std::optional<OwnerSnapshotQueue::Result> OwnerSnapshotQueue::Request::result() const
{
    std::lock_guard lock(mutex_);
    return result_;
}

void OwnerSnapshotQueue::Request::complete(Result result)
{
    std::lock_guard lock(mutex_);
    result_ = std::move(result);
}

std::shared_ptr<OwnerSnapshotQueue::Request> OwnerSnapshotQueue::request()
{
    auto reply = std::make_shared<Request>();
    std::lock_guard lock(mutex_);
    if (closed_) {
        reply->complete(std::unexpected("system_unavailable"));
    } else if (pending_ || reading_) {
        reply->complete(std::unexpected("busy"));
    } else {
        pending_ = reply;
    }
    return reply;
}

void OwnerSnapshotQueue::drain()
{
    std::shared_ptr<Request> reply;
    {
        std::lock_guard lock(mutex_);
        if (closed_ || reading_ || !pending_) { return; }
        reply.swap(pending_);
        reading_ = true;
    }
    auto result = reader_ ? reader_() : Result(std::unexpected("owner_unavailable"));
    {
        std::lock_guard lock(mutex_);
        if (closed_) { result = std::unexpected("system_unavailable"); }
        reply->complete(std::move(result));
        reading_ = false;
    }
}

void OwnerSnapshotQueue::close()
{
    std::shared_ptr<Request> reply;
    {
        std::lock_guard lock(mutex_);
        closed_ = true;
        reply.swap(pending_);
    }
    if (reply) { reply->complete(std::unexpected("system_unavailable")); }
}

} // namespace espocket
