// SPDX-License-Identifier: MIT
// Drag/spin/tilt/lean and friction adapted from The-Badge orb.c, without GUI globals.
#include "espocket/orbit_renderer.hpp"
#include <algorithm>
#include <cmath>
namespace espocket::orbit {
void Motion::reset() { *this = Motion{}; }
void Motion::cancel_touch()
{
    if (dragging_ || spin_ != 0 || tilt_velocity_ != 0 || lean_velocity_ != 0) dirty_ = true;
    dragging_ = false;
    spin_ = tilt_velocity_ = lean_velocity_ = 0;
}
Attitude Motion::attitude() const
{
    return {longitude_, tilt_, lean_, dragging_ || spin_ != 0 || tilt_velocity_ != 0 || lean_velocity_ != 0};
}
bool Motion::advance(unsigned elapsed_ms, Touch touch)
{
    constexpr float pi = 3.1415927f;
    const float dt = std::min(elapsed_ms, 200u) / 1000.0f;
    switch (touch.phase) {
    case Touch::Phase::Press:
        dragging_ = true; drag_x_ = touch.x; drag_y_ = touch.y;
        spin_ = tilt_velocity_ = lean_velocity_ = 0;
        break;
    case Touch::Phase::Move:
        if (dragging_) {
            const int dx = touch.x - drag_x_, dy = touch.y - drag_y_;
            drag_x_ = touch.x; drag_y_ = touch.y;
            if (dx || dy) {
                const float gx = std::clamp(static_cast<float>(touch.x - center) / radius, -1.0f, 1.0f);
                const float gy = std::clamp(static_cast<float>(touch.y - center) / radius, -1.0f, 1.0f);
                const float dln = (dx * -gy + dy * gx) / (2.0f * radius) * pi;
                const float cl = std::cos(lean_), sl = std::sin(lean_);
                const float bx = dx * cl + dy * sl, by = -dx * sl + dy * cl;
                const float bgx = gx * cl + gy * sl, bgy = -gx * sl + gy * cl;
                const float flip = std::cos(tilt_) >= 0 ? 1.0f : -1.0f;
                const float dl = -bx / (2.0f * radius) * 0.5f * flip * (1.0f - std::fabs(bgy));
                longitude_ += dl; spin_ = dl * 12.0f;
                lean_ += dln; lean_velocity_ = dln * 12.0f;
                const float tilt_delta = -by / (2.0f * radius) * pi * (1.0f - std::fabs(bgx));
                tilt_ += tilt_delta; tilt_velocity_ = tilt_delta * 12.0f;
                dirty_ = true;
            }
        }
        break;
    case Touch::Phase::Release: dragging_ = false; break;
    case Touch::Phase::Cancel: cancel_touch(); break;
    case Touch::Phase::None: break;
    }
    if (!dragging_) {
        spin_ *= std::pow(0.35f, dt);
        if (std::fabs(spin_) < 0.004f) spin_ = 0;
        longitude_ += spin_ * dt;
        tilt_velocity_ *= std::pow(0.30f, dt);
        if (std::fabs(tilt_velocity_) < 0.01f) tilt_velocity_ = 0;
        tilt_ += tilt_velocity_ * dt;
        lean_velocity_ *= std::pow(0.30f, dt);
        if (std::fabs(lean_velocity_) < 0.01f) lean_velocity_ = 0;
        lean_ += lean_velocity_ * dt;
    }
    while (tilt_ > pi) tilt_ -= 2 * pi;
    while (tilt_ < -pi) tilt_ += 2 * pi;
    while (lean_ > pi) lean_ -= 2 * pi;
    while (lean_ < -pi) lean_ += 2 * pi;
    longitude_ -= std::floor(longitude_);
    const bool moving = attitude().moving;
    const bool paint = moving || dirty_ || was_moving_;
    dirty_ = false; was_moving_ = moving;
    return paint; // One final sharp image, then no rendering while idle.
}
}
