#pragma once

#include <memory>
#include <mutex>
#include <optional>

#include "espocket/test_protocol.hpp"

namespace espocket {

// The transport submits; the serialized App owner samples between operations.
class OwnerSnapshotQueue {
public:
    using Result = std::expected<TestSnapshot, std::string>;
    class Request {
    public:
        std::optional<Result> result() const;
    private:
        friend class OwnerSnapshotQueue;
        void complete(Result result);
        mutable std::mutex mutex_;
        std::optional<Result> result_;
    };
    explicit OwnerSnapshotQueue(TestProtocol::SnapshotReader reader);
    std::shared_ptr<Request> request();
    void drain();
    void close();

private:
    TestProtocol::SnapshotReader reader_;
    std::mutex mutex_;
    std::shared_ptr<Request> pending_;
    bool reading_ = false;
    bool closed_ = false;
};

} // namespace espocket
