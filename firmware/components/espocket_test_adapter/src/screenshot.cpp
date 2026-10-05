#include "espocket/screenshot.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <stdexcept>

namespace espocket {

ScreenshotPixels::ScreenshotPixels(uint32_t width, uint32_t height, Allocate allocate)
    : width_(width), allocate_(std::move(allocate))
{
    if (!width || !height || width > 1024 || height > 1024 || !allocate_)
        throw std::invalid_argument("invalid screenshot dimensions or allocator");
    rows_.resize(height);
}

bool ScreenshotPixels::read_row(size_t index, std::span<uint8_t> destination) const
{
    if (index >= rows_.size() || destination.size() != width_ * 2) return false;
    const auto &row = rows_[index];
    if (!row.bytes) { std::fill(destination.begin(), destination.end(), 0); return true; }
    if (!row.rle) {
        if (row.size != destination.size()) return false;
        std::memcpy(destination.data(), row.bytes.get(), row.size);
        return true;
    }
    size_t pixel = 0;
    for (size_t i = 0; i < row.size; i += 4) {
        if (i + 4 > row.size) return false;
        const auto *run = row.bytes.get() + i;
        const size_t count = run[0] | (static_cast<size_t>(run[1]) << 8);
        if (!count || count > width_ - pixel) return false;
        for (size_t n = 0; n < count; ++n, ++pixel) {
            destination[pixel * 2] = run[2]; destination[pixel * 2 + 1] = run[3];
        }
    }
    return pixel == width_;
}

bool ScreenshotPixels::write(size_t offset, std::span<const uint8_t> source)
{
    if (offset > size() || source.size() > size() - offset) return false;
    const size_t row_bytes = width_ * 2;
    std::array<uint8_t, 2048> raw;
    while (!source.empty()) {
        const size_t index = offset / row_bytes, within = offset % row_bytes;
        const size_t count = std::min(source.size(), row_bytes - within);
        auto row_span = std::span(raw).first(row_bytes);
        if (!read_row(index, row_span)) return false;
        std::memcpy(raw.data() + within, source.data(), count);
        // Count runs first. Random pixels use raw storage without RLE expansion.
        size_t runs = 1;
        for (size_t p = 1; p < width_; ++p)
            runs += raw[p * 2] != raw[(p - 1) * 2] || raw[p * 2 + 1] != raw[(p - 1) * 2 + 1];
        const bool rle = runs * 4 < row_bytes;
        const size_t stored_bytes = rle ? runs * 4 : row_bytes;
        auto &row = rows_[index];
        // Reuse sufficiently large storage; repeated flush areas remain writable.
        const bool reuse = row.bytes && row.capacity >= stored_bytes;
        auto bytes = reuse ? row.bytes : allocate_(stored_bytes);
        if (!bytes) return false;
        if (!rle) std::memcpy(bytes.get(), raw.data(), row_bytes);
        else {
            size_t out = 0;
            for (size_t p = 0; p < width_;) {
                size_t end = p + 1;
                while (end < width_ && raw[end * 2] == raw[p * 2] && raw[end * 2 + 1] == raw[p * 2 + 1]) ++end;
                const size_t length = end - p;
                bytes.get()[out++] = static_cast<uint8_t>(length);
                bytes.get()[out++] = static_cast<uint8_t>(length >> 8);
                bytes.get()[out++] = raw[p * 2]; bytes.get()[out++] = raw[p * 2 + 1];
                p = end;
            }
        }
        row = {std::move(bytes), stored_bytes, reuse ? row.capacity : stored_bytes, rle};
        source = source.subspan(count); offset += count;
    }
    return true;
}

bool ScreenshotPixels::read(size_t offset, std::span<uint8_t> destination) const
{
    if (offset > size() || destination.size() > size() - offset) return false;
    std::array<uint8_t, 2048> raw;
    const size_t row_bytes = width_ * 2;
    while (!destination.empty()) {
        const size_t within = offset % row_bytes;
        const size_t count = std::min(destination.size(), row_bytes - within);
        if (!read_row(offset / row_bytes, std::span(raw).first(row_bytes))) return false;
        std::memcpy(destination.data(), raw.data() + within, count);
        destination = destination.subspan(count); offset += count;
    }
    return true;
}

size_t ScreenshotPixels::stored_size() const
{
    size_t total = 0;
    for (const auto &row : rows_) total += row.capacity;
    return total;
}

ScreenshotAssembly::ScreenshotAssembly(uint32_t width, uint32_t height,
                                       std::span<uint8_t> pixels, std::span<uint8_t> coverage)
    : width_(width), height_(height), pixels_(pixels), coverage_(coverage)
{
    const size_t count = static_cast<size_t>(width) * height;
    failed_ = width == 0 || height == 0 || width > 1024 || height > 1024 ||
              pixels.size() != count * 2 || coverage.size() != (count + 7) / 8;
    std::fill(coverage_.begin(), coverage_.end(), 0);
}

ScreenshotAssembly::ScreenshotAssembly(uint32_t width, uint32_t height,
                                       ScreenshotPixels &pixels, std::span<uint8_t> coverage)
    : width_(width), height_(height), coverage_(coverage), stored_pixels_(&pixels)
{
    const size_t count = static_cast<size_t>(width) * height;
    failed_ = !width || !height || width > 1024 || height > 1024 ||
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
        if (stored_pixels_) {
            if (!stored_pixels_->write(first * 2, source.subspan(row * stride, row_bytes))) {
                failed_ = true; return false;
            }
        } else std::memcpy(pixels_.data() + first * 2, source.data() + row * stride, row_bytes);
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
