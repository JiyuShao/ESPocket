#pragma once

#include <cstddef>
#include <cstdint>
#include <expected>
#include <memory>
#include <span>
#include <string>

namespace espocket {

struct TestScreenshot {
    uint32_t width = 0;
    uint32_t height = 0;
    size_t size = 0;
    std::shared_ptr<uint8_t> pixels;
    std::string sha256;
};

// RGB565 in native little-endian order, before the panel transport byte swap.
class ScreenshotAssembly {
public:
    ScreenshotAssembly(uint32_t width, uint32_t height, std::span<uint8_t> pixels,
                       std::span<uint8_t> coverage);
    bool append(int32_t x1, int32_t y1, int32_t x2, int32_t y2,
                std::span<const uint8_t> source, size_t stride);
    bool complete() const;

private:
    uint32_t width_, height_;
    std::span<uint8_t> pixels_, coverage_;
    size_t covered_ = 0;
    bool failed_ = false;
};

std::expected<TestScreenshot, std::string> capture_display_screenshot();

} // namespace espocket
