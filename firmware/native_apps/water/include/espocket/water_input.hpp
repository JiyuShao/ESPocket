#pragma once
#include "espocket/water_simulation.hpp"
#include <algorithm>
#include <optional>
#include <vector>
namespace espocket::water {
struct Point { int x, y; uint32_t track_id; };
class Input {
public:
    bool waiting_for_release() const { return wait_release_; }
    void cancel() { track_.reset(); wait_release_ = true; have_sequence_ = false; }
    Impulse read(bool valid, bool cancelled, uint32_t sequence, const std::vector<Point> &points)
    {
        if (!valid || cancelled) { cancel(); return {}; }
        if (have_sequence_ && sequence == sequence_) return {};
        have_sequence_ = true; sequence_ = sequence;
        if (wait_release_) { if (points.empty()) wait_release_ = false; return {}; }
        if (points.empty()) { track_.reset(); return {}; }
        const auto found = std::find_if(points.begin(), points.end(), [this](const auto &p) { return track_ && p.track_id == *track_; });
        if (track_ && found == points.end()) { cancel(); return {}; }
        const auto &point = track_ ? *found : points.front();
        const float dx = point.x - center, dy = point.y - center;
        if (dx * dx + dy * dy > bowl_radius * bowl_radius) { cancel(); return {}; }
        Impulse impulse{.x = static_cast<float>(point.x), .y = static_cast<float>(point.y), .active = true};
        if (!track_) { track_ = point.track_id; impulse.burst = 260; }
        else {
            impulse.vx = std::clamp((point.x - x_) * 8.0f, -400.0f, 400.0f);
            impulse.vy = std::clamp((point.y - y_) * 8.0f, -400.0f, 400.0f);
            impulse.active = impulse.vx != 0 || impulse.vy != 0;
        }
        x_ = point.x; y_ = point.y;
        return impulse;
    }
private:
    std::optional<uint32_t> track_;
    int x_ = 0, y_ = 0;
    uint32_t sequence_ = 0;
    bool have_sequence_ = false, wait_release_ = true;
};
}
