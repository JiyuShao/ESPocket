#pragma once
#include "espocket/orbit_renderer.hpp"
#include <algorithm>
#include <optional>
#include <vector>
namespace espocket::orbit {
struct Point { int x, y; uint32_t track_id; };
struct InputResult { Touch touch; std::optional<Kind> selection; bool activity = false; };
// Menu rectangles are shared by hit testing and the App-owned visual layout.
inline constexpr std::array<int, 4> menu_centers{134, 200, 266, 332};
inline std::optional<Kind> menu_hit(int x, int y)
{
    if (x < center - 125 || x >= center + 125) return {};
    for (int i = 0; i < 4; ++i) {
        // Respect the rounded 250x58 button (radius 29), including its corners.
        const int dx = std::max(0, std::abs(x - center) - 96), dy = y - menu_centers[i];
        if (dx * dx + dy * dy < 29 * 29) return static_cast<Kind>(i);
    }
    return {};
}
class Input {
public:
    void cancel() { track_.reset(); pick_.reset(); wait_release_ = true; have_sequence_ = false; }
    InputResult read(bool valid, bool cancelled, uint32_t sequence, const std::vector<Point> &points, bool viewer)
    {
        if (!valid || cancelled) { cancel(); return {{Touch::Phase::Cancel}, {}, false}; }
        if (have_sequence_ && sequence == sequence_) return {};
        have_sequence_ = true; sequence_ = sequence;
        if (wait_release_) { if (points.empty()) wait_release_ = false; return {}; }
        if (points.empty()) {
            if (!track_) return {};
            const auto selected = pick_;
            track_.reset(); pick_.reset();
            return {{Touch::Phase::Release}, selected, selected.has_value()};
        }
        const auto found = std::find_if(points.begin(), points.end(), [this](const auto &p) {
            return track_ && p.track_id == *track_;
        });
        if (track_ && found == points.end()) { cancel(); return {{Touch::Phase::Cancel}, {}, false}; }
        const auto &p = track_ ? *found : points.front();
        if (viewer) {
            const int64_t dx = static_cast<int64_t>(p.x) - center, dy = static_cast<int64_t>(p.y) - center;
            if (dx * dx + dy * dy > radius * radius) { cancel(); return {{Touch::Phase::Cancel}, {}, false}; }
        }
        const bool first = !track_;
        if (first) { track_ = p.track_id; pick_ = viewer ? std::nullopt : menu_hit(p.x, p.y); }
        else if (!viewer && pick_ != menu_hit(p.x, p.y)) pick_.reset();
        const bool moved = !first && (p.x != x_ || p.y != y_);
        x_ = p.x; y_ = p.y;
        return {{first ? Touch::Phase::Press : moved ? Touch::Phase::Move : Touch::Phase::None, p.x, p.y}, {},
            viewer ? first || moved : first && pick_.has_value()};
    }
private:
    std::optional<uint32_t> track_;
    std::optional<Kind> pick_;
    int x_ = 0, y_ = 0;
    uint32_t sequence_ = 0;
    bool have_sequence_ = false, wait_release_ = true;
};
}
