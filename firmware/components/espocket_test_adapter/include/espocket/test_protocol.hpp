#pragma once

#include <cstdint>
#include <mutex>
#include <functional>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include "espocket/developer_mode.hpp"
#include "espocket/touch_input_sequence.hpp"
#include "espocket/screenshot.hpp"

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
    bool navigation_available = true;
};

struct TestReply {
    bool ok = false;
    std::string error_code = {};
    std::string image_identity = {};
    std::vector<std::string> capabilities = {};
    std::optional<TestSnapshot> snapshot = std::nullopt;
    std::optional<TestScreenshot> screenshot = std::nullopt;
    uint64_t capture_id = 0;
    size_t offset = 0;
    std::string pixel_hex = {};
};

class TestProtocol {
public:
    static constexpr uint32_t VERSION = 1;
    using SnapshotReader = std::function<std::expected<TestSnapshot, std::string>()>;
    using TouchCommand = std::function<std::expected<void, std::string>(std::vector<TouchInputStep>)>;
    using Command = std::function<std::expected<void, std::string>()>;
    using ScreenshotReader = std::function<std::expected<TestScreenshot, std::string>()>;
    using Clock = std::function<uint64_t()>;

    TestProtocol(DeveloperMode &mode, std::string image_identity, SnapshotReader snapshot_reader = {},
                 Command power_short = {}, Command release = {}, TouchCommand touch = {},
                 ScreenshotReader screenshot_reader = {}, Clock clock = {});
    TestReply dispatch(uint32_t version, std::string_view operation, std::vector<TouchInputStep> steps = {},
                       uint64_t capture_id = 0, uint64_t offset = 0, uint64_t length = 0);
    void clear_screenshot();
    void expire_screenshot();

private:
    DeveloperMode &mode_;
    std::string image_identity_;
    std::mutex dispatch_mutex_;
    SnapshotReader snapshot_reader_;
    uint64_t snapshot_seq_ = 0;
    Command power_short_;
    Command release_;
    TouchCommand touch_;
    ScreenshotReader screenshot_reader_;
    Clock clock_;
    std::optional<TestScreenshot> screenshot_;
    uint64_t capture_id_ = 0;
    uint64_t expires_at_ = 0;
};

} // namespace espocket
