// SPDX-License-Identifier: MIT
#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <vector>
namespace espocket::brick {
// Geometry, level settings and per-20ms physics are from the locked The-Badge source.
inline constexpr int canvas_size = 466, center = 233, max_bricks = 36;
inline constexpr float ball_radius = 8, paddle_radius = 198;
struct Point { int x, y; uint32_t track_id; };
struct Tone { unsigned hz, ms; };
struct Brick { int x1 = 0, y1 = 0, x2 = 0, y2 = 0; uint32_t color = 0; uint8_t hp = 0; };
enum class Phase { Ready, Playing, Won };
struct State {
    std::array<Brick, max_bricks> bricks{};
    int brick_count = 0, remaining = 0, level = 0, lives = 3;
    float x = center, y = center + paddle_radius - 40, vx = 3, vy = -4;
    float paddle_angle = 180, paddle_half = 26, speed = 5, speed_start = 5, speed_max = 6.5;
    float obstacle_angle = 0, obstacle_step = 0;
    Phase phase = Phase::Ready;
};
class Model {
public:
    Model() { reset(); }
    void reset();
    void cancel_input();
    void suspend() { cancel_input(); accumulated_ms_ = 0; }
    std::vector<Tone> advance(uint32_t elapsed_ms, bool valid, bool cancelled,
        uint32_t sequence, const std::vector<Point> &points);
    const State &state() const { return state_; }
private:
    void rebuild();
    bool step(std::vector<Tone> &tones);
    bool input(bool valid, bool cancelled, uint32_t sequence, const std::vector<Point> &points);
    State state_;
    uint32_t accumulated_ms_ = 0, last_sequence_ = 0;
    bool have_sequence_ = false, wait_release_ = true, consume_touch_ = false;
    std::optional<uint32_t> grab_track_;
    float grab_angle_ = 0, grab_paddle_ = 0;
};
}
