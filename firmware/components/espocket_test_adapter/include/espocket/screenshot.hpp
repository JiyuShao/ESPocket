#pragma once

#include <cstddef>
#include <cstdint>
#include <expected>
#include <functional>
#include <memory>
#include <span>
#include <string>
#include <vector>

namespace espocket {

// Each row is stored as raw RGB565 or lossless (run length, RGB565) pairs,
// whichever is smaller. Capture never reserves a contiguous full-frame buffer.
class ScreenshotPixels {
public:
    using Allocate = std::function<std::shared_ptr<uint8_t>(size_t)>;
    ScreenshotPixels(uint32_t width, uint32_t height, Allocate allocate);
    bool write(size_t offset, std::span<const uint8_t> source);
    bool read(size_t offset, std::span<uint8_t> destination) const;
    size_t size() const { return static_cast<size_t>(width_) * rows_.size() * 2; }
    size_t stored_size() const;
private:
    struct Row { std::shared_ptr<uint8_t> bytes; size_t size = 0, capacity = 0; bool rle = false; };
    bool read_row(size_t index, std::span<uint8_t> destination) const;
    uint32_t width_;
    Allocate allocate_;
    std::vector<Row> rows_;
};

struct TestScreenshot {
    uint32_t width = 0;
    uint32_t height = 0;
    size_t size = 0;
    std::shared_ptr<ScreenshotPixels> pixels;
    std::string sha256;
};

// RGB565 in native little-endian order, before the panel transport byte swap.
class ScreenshotAssembly {
public:
    ScreenshotAssembly(uint32_t width, uint32_t height, std::span<uint8_t> pixels,
                       std::span<uint8_t> coverage);
    ScreenshotAssembly(uint32_t width, uint32_t height, ScreenshotPixels &pixels,
                       std::span<uint8_t> coverage);
    bool append(int32_t x1, int32_t y1, int32_t x2, int32_t y2,
                std::span<const uint8_t> source, size_t stride);
    bool complete() const;

private:
    uint32_t width_, height_;
    std::span<uint8_t> pixels_, coverage_;
    ScreenshotPixels *stored_pixels_ = nullptr;
    size_t covered_ = 0;
    bool failed_ = false;
};

std::expected<TestScreenshot, std::string> capture_display_screenshot();

} // namespace espocket
