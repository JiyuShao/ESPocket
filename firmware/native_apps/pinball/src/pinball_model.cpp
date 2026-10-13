// SPDX-License-Identifier: MIT
// Adapted from The-Badge app_games.c pinball section, locked in badge/upstream.lock.json.
#include "espocket/pinball_model.hpp"
#include <algorithm>
#include <cmath>
namespace espocket::pinball {
namespace {
constexpr float wall = 206, ball_radius = 6.5f, bumper_radius = 21, target_radius = 9;
constexpr float gravity = 0.085f, damping = 0.996f, wall_energy = 0.84f;
constexpr float flipper_length = 104, flipper_width = 14, flipper_step = 15, drain_half_width = 44;
constexpr float substeps = 3, radians = 0.0174533f;
float distance(float x, float y) { return std::sqrt(x * x + y * y); }
}
void Model::reset()
{
    state_ = {};
    state_.x = center + 96; state_.y = center - 150; state_.vx = -1.2f; state_.vy = 0.6f;
    constexpr float bx[bumper_count] = {0, -78, 78, -46, 46};
    constexpr float by[bumper_count] = {-128, -58, -58, 26, 26};
    constexpr float tx[target_count] = {-150, -150, 150, 150};
    constexpr float ty[target_count] = {-78, -34, -78, -34};
    for (int i = 0; i < bumper_count; ++i) { state_.bumper_x[i] = center + bx[i]; state_.bumper_y[i] = center + by[i]; }
    for (int i = 0; i < target_count; ++i) { state_.target_x[i] = center + tx[i]; state_.target_y[i] = center + ty[i]; state_.target_up[i] = true; }
    state_.flippers[0] = {center - 141, center + 150, 24, -34, 24, false};
    state_.flippers[1] = {center + 141, center + 150, 156, 214, 156, false};
    state_.phase = Phase::Ready; accumulated_ms_ = 0; cancel_input();
}
void Model::cancel_input()
{
    state_.flippers[0].on = state_.flippers[1].on = false;
    have_sequence_ = false; wait_release_ = true; consume_touch_ = false;
}
bool Model::input(bool valid, bool cancelled, uint32_t sequence, const std::vector<Point> &points)
{
    if (!valid || cancelled) { cancel_input(); return false; }
    if (have_sequence_ && sequence == last_sequence_) return false;
    have_sequence_ = true; last_sequence_ = sequence;
    if (wait_release_) { if (points.empty()) wait_release_ = false; return false; }
    if (points.empty()) { state_.flippers[0].on = state_.flippers[1].on = false; consume_touch_ = false; return false; }
    if (state_.phase != Phase::Playing) {
        if (state_.phase == Phase::GameOver) reset();
        state_.phase = Phase::Playing; consume_touch_ = true; return true;
    }
    if (consume_touch_) return false; // release the start frame before flipper input
    state_.flippers[0].on = state_.flippers[1].on = false;
    for (const auto &point : points) {
        if (point.x < center) state_.flippers[0].on = true;
        else state_.flippers[1].on = true;
    }
    return false;
}
void Model::lose_ball(std::vector<Tone> &tones)
{
    if (state_.balls > 0) --state_.balls;
    tones.push_back({180, 120});
    if (state_.balls == 0) { state_.phase = Phase::GameOver; accumulated_ms_ = 0; cancel_input(); return; }
    state_.x = center + 96; state_.y = center - 150; state_.vx = -1.2f; state_.vy = 0.6f;
}
bool Model::substep(std::vector<Tone> &tones, const std::array<float, 2> &omega, std::array<bool, 2> &kicked)
{
    state_.x += state_.vx / substeps; state_.y += state_.vy / substeps;
    for (int i = 0; i < bumper_count; ++i) {
        const float dx = state_.x - state_.bumper_x[i], dy = state_.y - state_.bumper_y[i];
        const float hit = bumper_radius + ball_radius, d2 = dx * dx + dy * dy;
        if (d2 >= hit * hit || d2 < 0.01f) continue;
        const float d = std::sqrt(d2), nx = dx / d, ny = dy / d;
        state_.x = state_.bumper_x[i] + nx * hit; state_.y = state_.bumper_y[i] + ny * hit;
        const float dot = state_.vx * nx + state_.vy * ny;
        state_.vx -= 2.3f * dot * nx; state_.vy -= 2.3f * dot * ny;
        state_.points += 10; tones.push_back({1100, 30}); break;
    }
    for (int i = 0; i < target_count; ++i) {
        if (!state_.target_up[i]) continue;
        const float dx = state_.x - state_.target_x[i], dy = state_.y - state_.target_y[i];
        const float hit = target_radius + ball_radius, d2 = dx * dx + dy * dy;
        if (d2 >= hit * hit || d2 < 0.01f) continue;
        const float d = std::sqrt(d2), nx = dx / d, ny = dy / d;
        state_.x = state_.target_x[i] + nx * hit; state_.y = state_.target_y[i] + ny * hit;
        const float dot = state_.vx * nx + state_.vy * ny;
        state_.vx -= 1.6f * dot * nx; state_.vy -= 1.6f * dot * ny;
        state_.target_up[i] = false; state_.points += 50; tones.push_back({1400, 40});
        bool any = false; for (bool up : state_.target_up) any |= up;
        if (!any) { state_.points += 200; state_.target_up.fill(true); tones.push_back({1600, 90}); }
        break;
    }
    for (int i = 0; i < 2; ++i) {
        const auto &f = state_.flippers[i]; const float a = f.angle * radians;
        const float ex = std::cos(a), ey = std::sin(a);
        const float rx = state_.x - f.px, ry = state_.y - f.py;
        const float t = std::clamp(rx * ex + ry * ey, 0.0f, flipper_length);
        const float cx = f.px + ex * t, cy = f.py + ey * t;
        const float dx = state_.x - cx, dy = state_.y - cy, d2 = dx * dx + dy * dy;
        const float hit = ball_radius + flipper_width * 0.5f;
        if (d2 >= hit * hit || d2 < 0.01f || kicked[i]) continue;
        const float d = std::sqrt(d2), nx = dx / d, ny = dy / d;
        state_.x = cx + nx * hit; state_.y = cy + ny * hit;
        const float dot = state_.vx * nx + state_.vy * ny;
        if (dot < 0) { state_.vx -= 1.75f * dot * nx; state_.vy -= 1.75f * dot * ny; }
        const float w = omega[i] * radians;
        state_.vx += -ey * w * t; state_.vy += ex * w * t;
        kicked[i] = true; tones.push_back({420, 24});
    }
    const float dx = state_.x - center, dy = state_.y - center, r = distance(dx, dy);
    if (r > wall) {
        if (dy > 0 && std::fabs(dx) < drain_half_width) { lose_ball(tones); return false; }
        const float nx = dx / r, ny = dy / r, dot = state_.vx * nx + state_.vy * ny;
        state_.vx -= (1 + wall_energy) * dot * nx; state_.vy -= (1 + wall_energy) * dot * ny;
        state_.x = center + nx * wall; state_.y = center + ny * wall;
    }
    return state_.phase == Phase::Playing;
}
bool Model::step(std::vector<Tone> &tones)
{
    state_.vy += gravity; state_.vx *= damping; state_.vy *= damping;
    std::array<float, 2> omega{}; std::array<bool, 2> kicked{};
    for (int i = 0; i < 2; ++i) {
        const float want = state_.flippers[i].on ? state_.flippers[i].up : state_.flippers[i].rest;
        omega[i] = std::clamp(want - state_.flippers[i].angle, -flipper_step, flipper_step);
    }
    for (int i = 0; i < 2; ++i) state_.flippers[i].angle += omega[i] / substeps;
    for (int i = 0; i < substeps; ++i) if (!substep(tones, omega, kicked)) return false;
    return true;
}
std::vector<Tone> Model::advance(uint32_t elapsed, bool valid, bool cancelled, uint32_t sequence, const std::vector<Point> &points)
{
    std::vector<Tone> tones;
    if (input(valid, cancelled, sequence, points) || state_.phase != Phase::Playing) return tones;
    accumulated_ms_ = std::min<uint32_t>(200, accumulated_ms_ + std::min<uint32_t>(elapsed, 200));
    for (int steps = 0; accumulated_ms_ >= 20 && steps < 5; ++steps) { accumulated_ms_ -= 20; if (!step(tones)) break; }
    return tones;
}
}
