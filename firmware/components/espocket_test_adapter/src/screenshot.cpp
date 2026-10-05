#include "espocket/screenshot.hpp"

#include <algorithm>
#include <cstring>

namespace espocket {

ScreenshotAssembly::ScreenshotAssembly(uint32_t width, uint32_t height,
                                       std::span<uint8_t> pixels, std::span<uint8_t> coverage)
    : width_(width), height_(height), pixels_(pixels), coverage_(coverage)
{
    const size_t count = static_cast<size_t>(width) * height;
    failed_ = width == 0 || height == 0 || width > 1024 || height > 1024 ||
              pixels.size() != count * 2 || coverage.size() != (count + 7) / 8;
    std::fill(coverage_.begin(), coverage_.end(), 0);
}

bool ScreenshotAssembly::append(int32_t x1, int32_t y1, int32_t x2, int32_t y2,
                                std::span<const uint8_t> source, size_t stride)
{
    if (failed_) return false;
    if (x1 < 0 || y1 < 0 || x2 < x1 || y2 < y1 ||
            x2 >= static_cast<int32_t>(width_) || y2 >= static_cast<int32_t>(height_)) {
        failed_ = true;
        return false;
    }
    const size_t row_bytes = static_cast<size_t>(x2 - x1 + 1) * 2;
    const size_t rows = static_cast<size_t>(y2 - y1 + 1);
    if (stride < row_bytes || stride > source.size() ||
            rows - 1 > (source.size() - row_bytes) / stride) {
        failed_ = true;
        return false;
    }
    for (size_t row = 0; row < rows; ++row) {
        const size_t first = (static_cast<size_t>(y1) + row) * width_ + x1;
        std::memcpy(pixels_.data() + first * 2, source.data() + row * stride, row_bytes);
        for (size_t i = first; i < first + row_bytes / 2; ++i) {
            const uint8_t mask = static_cast<uint8_t>(1U << (i % 8));
            if (!(coverage_[i / 8] & mask)) {
                coverage_[i / 8] |= mask;
                ++covered_;
            }
        }
    }
    return true;
}

bool ScreenshotAssembly::complete() const
{
    return !failed_ && covered_ == static_cast<size_t>(width_) * height_;
}

} // namespace espocket
