#pragma once

#include <cstdint>
#include <mutex>
#include <functional>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include "espocket/developer_mode.hpp"

namespace espocket {

struct TestSnapshot {
    uint64_t seq = 0;
    std::string surface;
    bool display = false;
    std::string foreground_app_id;
    std::string page_id;
    bool can_back = false;
    bool back_pending = false;
    bool input_busy = false;
};

struct TestReply {
    bool ok = false;
    std::string error_code;
    std::string image_identity;
    std::vector<std::string> capabilities;
    std::optional<TestSnapshot> snapshot = std::nullopt;
};

class TestProtocol {
public:
    static constexpr uint32_t VERSION = 1;
    using SnapshotReader = std::function<std::expected<TestSnapshot, std::string>()>;
    using Command = std::function<std::expected<void, std::string>()>;

    TestProtocol(DeveloperMode &mode, std::string image_identity, SnapshotReader snapshot_reader = {},
                 Command power_short = {}, Command release = {});
    TestReply dispatch(uint32_t version, std::string_view operation);

private:
    DeveloperMode &mode_;
    std::string image_identity_;
    std::mutex dispatch_mutex_;
    SnapshotReader snapshot_reader_;
    uint64_t snapshot_seq_ = 0;
    Command power_short_;
    Command release_;
};

} // namespace espocket
