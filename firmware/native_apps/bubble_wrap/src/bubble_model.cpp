// SPDX-License-Identifier: MIT
// Original: The-Badge main/apps/app_games.c, bubble-wrap section.
#include "espocket/bubble_model.hpp"
#include <algorithm>
namespace espocket::bubble {
Model::Model() { reset(); }
void Model::reset()
{
    cells_.clear(); holds_.clear(); has_sequence_ = false; refill_ms_ = 0; seed_ = 2463534242u;
    // Original 466px board, 78px bubbles, staggered 82x70 grid, radius 178.
    for (int row = -2; row <= 2; ++row) {
        const int offset = (row & 1) ? 41 : 0;
        for (int col = -2; col <= 2; ++col) {
            const int dx = col * 82 + offset, dy = row * 70;
            if (dx * dx + dy * dy <= 178 * 178) cells_.push_back({233 + dx, 233 + dy});
        }
    }
    remaining_ = static_cast<int>(cells_.size());
}
void Model::cancel_input() { holds_.clear(); has_sequence_ = false; }
uint32_t Model::random()
{
    seed_ ^= seed_ << 13; seed_ ^= seed_ >> 17; seed_ ^= seed_ << 5; return seed_;
}
Tone Model::refill()
{
    for (auto &cell : cells_) cell.popped = false;
    remaining_ = static_cast<int>(cells_.size()); refill_ms_ = 0;
    return {520, 130};
}
std::vector<Tone> Model::advance(uint32_t elapsed_ms, bool valid, bool cancelled,
                                uint32_t sequence, const std::vector<Point> &points)
{
    std::vector<Tone> tones;
    if (refill_ms_ != 0) {
        if (elapsed_ms >= refill_ms_) tones.push_back(refill());
        else refill_ms_ -= elapsed_ms;
    }
    if (!valid || cancelled) { cancel_input(); return tones; }
    const bool fresh = !has_sequence_ || sequence != last_sequence_;
    if (fresh) {
        last_sequence_ = sequence; has_sequence_ = true;
        // Release and movement invalidate a hold before evaluating its deadline.
        std::erase_if(holds_, [&](const Hold &hold) {
            return std::none_of(points.begin(), points.end(), [&](const Point &point) { return point.track_id == hold.id; });
        });
        for (auto &hold : holds_) {
            const auto point = std::find_if(points.begin(), points.end(), [&](const Point &point) { return point.track_id == hold.id; });
            const int dx = point->x - hold.x, dy = point->y - hold.y;
            if (dx * dx + dy * dy > 100) hold.background = false;
        }
    }
    for (auto &hold : holds_) {
        hold.elapsed += elapsed_ms;
        if (hold.background && !hold.refilled && hold.elapsed >= 550) {
            tones.push_back(refill()); hold.refilled = true;
        }
    }
    if (!fresh) return tones;
    for (const auto &point : points) {
        auto held = std::find_if(holds_.begin(), holds_.end(), [&](const Hold &hold) { return hold.id == point.track_id; });
        if (held != holds_.end()) {
            const int dx = point.x - held->x, dy = point.y - held->y;
            if (dx * dx + dy * dy > 100) held->background = false; // drag cancels long press
            continue;
        }
        auto cell = std::find_if(cells_.begin(), cells_.end(), [&](const Cell &cell) {
            const int size = cell.popped ? 54 : 78;
            return point.x >= cell.x - 39 && point.x < cell.x - 39 + size &&
                   point.y >= cell.y - 39 && point.y < cell.y - 39 + size;
        });
        holds_.push_back({point.track_id, point.x, point.y, 0, cell == cells_.end(), false});
        if (cell == cells_.end() || cell->popped) continue;
        cell->popped = true; --remaining_;
        tones.push_back({760 + random() % 620, 22});
        if (remaining_ == 0) refill_ms_ = 7 * 120;
    }
    return tones;
}
}
