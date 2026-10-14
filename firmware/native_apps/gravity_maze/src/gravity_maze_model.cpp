#include "espocket/gravity_maze_model.hpp"
#include <algorithm>
#include <cmath>

namespace espocket::gravity_maze {
namespace {
constexpr float acceleration_scale = 0.00032f;
constexpr float friction = 0.965f;
constexpr float maximum_speed = 7.0f;
constexpr float hole_radius = 30.0f;
constexpr float degrees_to_radians = 0.01745329252f;
}

Model::Model() { reset(); }

void Model::reset()
{
    state_ = {};
    state_.marble_x = state_.marble_y = static_cast<float>(center);
    state_.velocity_x = state_.velocity_y = 0;
    state_.score = 0;
    have_reference_ = false;
    cancel_input();
    new_hole();
}

void Model::cancel_input()
{
    have_sequence_ = false;
    wait_release_ = true;
}

uint32_t Model::random()
{
    seed_ ^= seed_ << 13; seed_ ^= seed_ >> 17; seed_ ^= seed_ << 5; return seed_;
}

void Model::new_hole()
{
    const float angle = static_cast<float>(random() % 360) * degrees_to_radians;
    const float radius = 50.0f + static_cast<float>(random() % 120);
    state_.hole_x = static_cast<float>(center) + std::cos(angle) * radius;
    state_.hole_y = static_cast<float>(center) + std::sin(angle) * radius;
}

void Model::advance(uint32_t elapsed_ms, bool valid, bool cancelled, uint32_t sequence,
                   const std::vector<Point> &points, std::optional<imu::Sample> sample)
{
    if (!valid || cancelled) { cancel_input(); return; }
    const bool fresh = !have_sequence_ || sequence != last_sequence_;
    if (fresh) { have_sequence_ = true; last_sequence_ = sequence; }
    if (wait_release_) {
        if (points.empty()) wait_release_ = false;
        return;
    }
    if (!fresh) return;

    float ax = 0, ay = 0;
    if (sample && sample->accel_valid) {
        if (!have_reference_) {
            reference_x_ = sample->accel_x_mg; reference_y_ = sample->accel_y_mg;
            have_reference_ = true;
        }
        // The board is mounted a quarter turn from the display. This mapping is
        // part of the board contract and remains isolated in the game model.
        ax = (sample->accel_y_mg - reference_y_);
        ay = (sample->accel_x_mg - reference_x_);
    } else if (!points.empty()) {
        // Explicit touch fallback used when the board reports unavailable/invalid.
        ax = -(static_cast<float>(points.front().y) - center) * 4.0f;
        ay = -(static_cast<float>(points.front().x) - center) * 4.0f;
    }
    state_.velocity_x -= ax * acceleration_scale;
    state_.velocity_y -= ay * acceleration_scale;
    state_.velocity_x *= friction; state_.velocity_y *= friction;
    const float speed = std::sqrt(state_.velocity_x * state_.velocity_x + state_.velocity_y * state_.velocity_y);
    if (speed > maximum_speed) {
        state_.velocity_x = state_.velocity_x / speed * maximum_speed;
        state_.velocity_y = state_.velocity_y / speed * maximum_speed;
    }
    const auto steps = std::min<uint32_t>(8, std::max<uint32_t>(1, elapsed_ms / 8));
    for (uint32_t i = 0; i < steps; ++i) {
        state_.marble_x += state_.velocity_x / static_cast<float>(steps);
        state_.marble_y += state_.velocity_y / static_cast<float>(steps);
        const float dx = state_.marble_x - center, dy = state_.marble_y - center;
        const float radius = std::sqrt(dx * dx + dy * dy);
        if (radius > rim_radius) {
            const float nx = dx / radius, ny = dy / radius;
            const float dot = state_.velocity_x * nx + state_.velocity_y * ny;
            state_.velocity_x = (state_.velocity_x - 2 * dot * nx) * 0.45f;
            state_.velocity_y = (state_.velocity_y - 2 * dot * ny) * 0.45f;
            state_.marble_x = center + nx * (rim_radius - 1);
            state_.marble_y = center + ny * (rim_radius - 1);
        }
    }
    const float hx = state_.marble_x - state_.hole_x, hy = state_.marble_y - state_.hole_y;
    if (hx * hx + hy * hy < hole_radius * hole_radius) {
        ++state_.score; state_.velocity_x = state_.velocity_y = 0; new_hole();
    }
}
} // namespace espocket::gravity_maze
