#include "espocket/test_protocol.hpp"
#include <array>

#include <utility>
#include <chrono>

namespace espocket {

TestProtocol::TestProtocol(DeveloperMode &mode, std::string image_identity, SnapshotReader snapshot_reader,
                           Command power_short, Command release, TouchCommand touch,
                           ScreenshotReader screenshot_reader, Clock clock)
    : mode_(mode), image_identity_(std::move(image_identity)),
      snapshot_reader_(std::move(snapshot_reader)), power_short_(std::move(power_short)),
      release_(std::move(release)), touch_(std::move(touch)),
      screenshot_reader_(std::move(screenshot_reader)), clock_(std::move(clock))
{
    if (!clock_) clock_ = [] { return static_cast<uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count()); };
}

void TestProtocol::clear_screenshot()
{
    std::lock_guard lock(dispatch_mutex_);
    screenshot_.reset();
}

void TestProtocol::expire_screenshot()
{
    std::lock_guard lock(dispatch_mutex_);
    if (screenshot_ && clock_() >= expires_at_) screenshot_.reset();
}

TestReply TestProtocol::dispatch(uint32_t version, std::string_view operation, std::vector<TouchInputStep> steps,
                               uint64_t capture_id, uint64_t offset, uint64_t length)
{
    std::unique_lock lock(dispatch_mutex_, std::try_to_lock);
    if (!lock.owns_lock()) {
        return {.ok = false, .error_code = "busy", .image_identity = {}, .capabilities = {}};
    }
    if (version != VERSION) {
        return {.ok = false, .error_code = "bad_request", .image_identity = {}, .capabilities = {}};
    }
    if (!mode_.enabled()) {
        screenshot_.reset();
        return {.ok = false, .error_code = "developer_mode_off", .image_identity = {}, .capabilities = {}};
    }
    if (operation == "hello") {
        std::vector<std::string> capabilities = {"hello"};
        if (snapshot_reader_) {
            capabilities.emplace_back("snapshot");
        }
        if (power_short_) { capabilities.emplace_back("stimulus.powerShort"); }
        if (touch_) { capabilities.emplace_back("stimulus.touch"); }
        if (release_) { capabilities.emplace_back("release"); }
        if (screenshot_reader_) {
            capabilities.emplace_back("screenshot");
            capabilities.emplace_back("screenshot.read");
        }
        return {
            .ok = true,
            .error_code = {},
            .image_identity = image_identity_,
            .capabilities = std::move(capabilities),
        };
    }
    if (operation == "screenshot" && screenshot_reader_) {
        screenshot_.reset();
        auto captured = screenshot_reader_();
        if (!captured) return {.ok = false, .error_code = captured.error()};
        if (!mode_.enabled()) return {.ok = false, .error_code = "developer_mode_off"};
        if (!captured->pixels || captured->pixels->size() != captured->size || captured->width == 0 || captured->height == 0 ||
                captured->width > 1024 || captured->height > 1024 ||
                captured->size != static_cast<size_t>(captured->width) * captured->height * 2 ||
                captured->sha256.size() != 64) return {.ok = false, .error_code = "internal"};
        screenshot_ = std::move(*captured);
        ++capture_id_;
        expires_at_ = clock_() + 60'000;
        return {.ok = true, .screenshot = screenshot_, .capture_id = capture_id_};
    }
    if (operation == "screenshot.read" && screenshot_reader_) {
        if (screenshot_ && clock_() >= expires_at_) screenshot_.reset();
        if (!screenshot_ || capture_id != capture_id_) return {.ok = false, .error_code = "invalid_state"};
        if (length == 0 || length > 512 || offset >= screenshot_->size ||
                length > screenshot_->size - offset) return {.ok = false, .error_code = "bad_request"};
        constexpr char hex[] = "0123456789abcdef";
        std::string pixels;
        pixels.reserve(static_cast<size_t>(length) * 2);
        std::array<uint8_t, 512> bytes;
        if (!screenshot_->pixels->read(offset, std::span(bytes).first(length)))
            return {.ok = false, .error_code = "internal"};
        for (size_t i = static_cast<size_t>(offset); i < offset + length; ++i) {
            const auto byte = bytes[i - offset];
            pixels += hex[byte >> 4]; pixels += hex[byte & 15];
        }
        return {.ok = true, .capture_id = capture_id_, .offset = static_cast<size_t>(offset),
                .pixel_hex = std::move(pixels)};
    }
    if (operation == "snapshot" && snapshot_reader_) {
        auto snapshot = snapshot_reader_();
        if (!snapshot) {
            return {.ok = false, .error_code = "invalid_state", .image_identity = {}, .capabilities = {}};
        }
        snapshot->seq = ++snapshot_seq_;
        return {.ok = true, .error_code = {}, .image_identity = {}, .capabilities = {},
                .snapshot = std::move(*snapshot)};
    }
    if (operation == "stimulus.touch" && touch_) {
        auto result = touch_(std::move(steps));
        return {.ok = result.has_value(), .error_code = result ? "" : result.error(),
                .image_identity = {}, .capabilities = {}};
    }
    const Command *command = nullptr;
    if (operation == "stimulus.powerShort" && power_short_) { command = &power_short_; }
    if (operation == "release" && release_) { command = &release_; }
    if (command) {
        if (operation == "release") screenshot_.reset();
        auto result = (*command)();
        return {.ok = result.has_value(), .error_code = result ? "" : result.error(),
                .image_identity = {}, .capabilities = {}};
    }
    return {.ok = false, .error_code = "unsupported", .image_identity = {}, .capabilities = {}};
}

} // namespace espocket
