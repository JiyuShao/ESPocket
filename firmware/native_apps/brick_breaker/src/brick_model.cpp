// SPDX-License-Identifier: MIT
// Adapted from The-Badge main/apps/app_games.c, commit recorded in badge/upstream.lock.json.
#include "espocket/brick_model.hpp"
#include <algorithm>
#include <cmath>
namespace espocket::brick {
namespace {
constexpr float radians = 0.0174533f, paddle_min = 128, paddle_max = 232;
struct Level { float start, cap, half; int rows, pattern, tough; float obstacle; };
constexpr std::array<Level, 5> levels{{
    {5, 6.5, 26, 3, 0, 0, 0}, {5.4, 7, 24, 4, 0, 1, 0},
    {5.8, 7.5, 22, 4, 1, 2, 1.2}, {6.4, 8.2, 20, 4, 2, 2, 1.8},
    {7, 9, 18, 4, 0, 2, 2.6}
}};
float angle(float x, float y)
{
    float value = std::atan2(x - center, center - y) / radians;
    return value < 0 ? value + 360 : value;
}
}
void Model::reset()
{
    state_ = {}; rebuild(); cancel_input();
}
void Model::cancel_input()
{
    grab_track_.reset(); have_sequence_ = false; wait_release_ = true; consume_touch_ = false;
}
void Model::rebuild()
{
    const auto &level = levels[state_.level];
    state_.speed_start = state_.speed = level.start; state_.speed_max = level.cap;
    state_.paddle_half = level.half; state_.obstacle_step = level.obstacle; state_.obstacle_angle = 0;
    state_.paddle_angle = 180; state_.x = center; state_.y = center + paddle_radius - 40;
    state_.vx = level.start * 0.6f; state_.vy = -level.start * 0.8f;
    state_.bricks = {}; state_.brick_count = 0;
    constexpr std::array<uint32_t, 4> colors{0x7FB0FF, 0x5BD48A, 0xE0A33A, 0xC98BE0};
    constexpr int height = 26, gap = 4;
    constexpr float fit = paddle_radius + ball_radius - 4;
    for (int row = 0; row < level.rows; ++row) {
        const int y = 80 + row * (height + gap);
        const float far = std::max(std::fabs(float(y - center)), std::fabs(float(y + height - center)));
        const int total = 2 * static_cast<int>(std::sqrt(std::max(0.0f, fit * fit - far * far)));
        const int count = std::min(9, total / 62);
        if (count < 1) continue;
        const int width = (total - gap * (count - 1)) / count;
        for (int k = 0; k < count; ++k) {
            if ((level.pattern == 1 && ((row + k) & 1)) || (level.pattern == 2 && count >= 5 && k == count / 2)) continue;
            const int x = center - total / 2 + k * (width + gap);
            state_.bricks[state_.brick_count++] = {x, y, x + width, y + height, colors[row],
                static_cast<uint8_t>(row < level.tough ? 2 : 1)};
        }
    }
    state_.remaining = state_.brick_count; state_.phase = Phase::Ready;
    accumulated_ms_ = 0;
    // A level/miss transition cannot reuse the drag that was already down.
    cancel_input();
}
bool Model::input(bool valid, bool cancelled, uint32_t sequence, const std::vector<Point> &points)
{
    if (!valid || cancelled) { cancel_input(); return false; }
    if (have_sequence_ && sequence == last_sequence_) return false;
    have_sequence_ = true; last_sequence_ = sequence;
    if (wait_release_) { if (points.empty()) wait_release_ = false; return false; }
    if (points.empty()) { grab_track_.reset(); consume_touch_ = false; return false; }
    if (consume_touch_) return false;
    if (state_.phase != Phase::Playing) {
        if (state_.phase == Phase::Won) reset();
        state_.phase = Phase::Playing; accumulated_ms_ = 0; consume_touch_ = true; wait_release_ = false;
        return true; // Starting tap is consumed; physics starts on the next tick.
    }
    if (!grab_track_) {
        grab_track_ = points.front().track_id; grab_angle_ = angle(points.front().x, points.front().y);
        grab_paddle_ = state_.paddle_angle; return false;
    }
    const auto point = std::find_if(points.begin(), points.end(), [this](const auto &p) { return p.track_id == *grab_track_; });
    if (point == points.end()) { grab_track_.reset(); wait_release_ = true; return false; }
    float delta = angle(point->x, point->y) - grab_angle_;
    while (delta > 180) delta -= 360;
    while (delta < -180) delta += 360;
    state_.paddle_angle = std::clamp(grab_paddle_ + delta * 1.5f, paddle_min, paddle_max);
    return false;
}
std::vector<Tone> Model::advance(uint32_t elapsed, bool valid, bool cancelled, uint32_t sequence, const std::vector<Point> &points)
{
    std::vector<Tone> tones;
    if (input(valid, cancelled, sequence, points) || state_.phase != Phase::Playing) return tones;
    // Keep the source's bounded 20ms stepping: at most 200ms accrual and five steps per frame.
    accumulated_ms_ = std::min<uint32_t>(200, accumulated_ms_ + std::min<uint32_t>(elapsed, 200));
    for (int steps = 0; accumulated_ms_ >= 20 && steps < 5; ++steps) {
        accumulated_ms_ -= 20;
        if (!step(tones)) break;
    }
    return tones;
}
bool Model::step(std::vector<Tone> &tones)
{
    auto &s = state_;
    if (s.obstacle_step > 0) { s.obstacle_angle += s.obstacle_step; if (s.obstacle_angle >= 360) s.obstacle_angle -= 360; }
    s.x += s.vx; s.y += s.vy;
    const float dx = s.x - center, dy = s.y - center, radius = std::sqrt(dx * dx + dy * dy);
    const float ball_angle = angle(s.x, s.y);
    bool hit_brick = false;
    for (int i = 0; i < s.brick_count; ++i) {
        auto &b = s.bricks[i];
        if (!b.hp || s.x < b.x1 - ball_radius || s.x > b.x2 + ball_radius ||
            s.y < b.y1 - ball_radius || s.y > b.y2 + ball_radius) continue;
        if (--b.hp) tones.push_back({600, 30});
        else { --s.remaining; tones.push_back({900, 40}); }
        const float right = b.x2 + ball_radius - s.x, left = s.x - (b.x1 - ball_radius);
        const float down = b.y2 + ball_radius - s.y, up = s.y - (b.y1 - ball_radius);
        if (std::min(right, left) < std::min(down, up)) { s.vx = -s.vx; s.x += right < left ? right : -left; }
        else { s.vy = -s.vy; s.y += down < up ? down : -up; }
        hit_brick = true; break;
    }
    if (s.obstacle_step > 0) {
        constexpr float hit_radius = 13 + ball_radius;
        for (int i = 0; i < 2; ++i) {
            const float a = (s.obstacle_angle + i * 180) * radians;
            const float ox = center + std::sin(a) * 124, oy = center - std::cos(a) * 124;
            const float ex = s.x - ox, ey = s.y - oy, distance2 = ex * ex + ey * ey;
            if (distance2 >= hit_radius * hit_radius || distance2 < 0.01f) continue;
            const float distance = std::sqrt(distance2), nx = ex / distance, ny = ey / distance;
            const float dot = s.vx * nx + s.vy * ny;
            if (dot < 0) { s.vx -= 2 * dot * nx; s.vy -= 2 * dot * ny; }
            s.x = ox + nx * hit_radius; s.y = oy + ny * hit_radius;
            tones.push_back({700, 25}); break;
        }
    }
    // Original collision ordering: a brick reflection must not be reflected by the wall again.
    if (!hit_brick && radius > paddle_radius) {
        const bool bottom = ball_angle > paddle_min - 8 && ball_angle < paddle_max + 8;
        float delta = std::fabs(ball_angle - s.paddle_angle);
        if (delta > 180) delta = 360 - delta;
        if (!bottom || delta < s.paddle_half) {
            const float nx = dx / radius, ny = dy / radius, dot = s.vx * nx + s.vy * ny;
            s.vx -= 2 * dot * nx; s.vy -= 2 * dot * ny;
            if (bottom) {
                s.vx += (ball_angle - s.paddle_angle) / s.paddle_half * 1.1f;
                s.speed = std::min(std::max(s.speed, s.speed_start) * 1.015f, s.speed_max);
                const float magnitude = std::sqrt(s.vx * s.vx + s.vy * s.vy);
                if (magnitude > 0.01f) { s.vx = s.vx / magnitude * s.speed; s.vy = s.vy / magnitude * s.speed; }
                tones.push_back({500, 30});
            }
            s.x = center + nx * (paddle_radius - (bottom ? 3 : 2));
            s.y = center + ny * (paddle_radius - (bottom ? 3 : 2));
        } else if (radius > 224) {
            if (--s.lives == 0) { s.lives = 3; s.level = 0; }
            rebuild(); return false;
        }
    }
    if (!s.remaining) {
        if (s.level + 1 < static_cast<int>(levels.size())) { ++s.level; rebuild(); }
        else { s.phase = Phase::Won; accumulated_ms_ = 0; cancel_input(); }
        return false;
    }
    return true;
}
}
