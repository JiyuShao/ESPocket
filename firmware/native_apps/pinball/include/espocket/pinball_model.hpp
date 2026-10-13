// SPDX-License-Identifier: MIT
#pragma once
#include <array>
#include <cstdint>
#include <vector>
namespace espocket::pinball {
inline constexpr int center = 233, canvas_size = 466, bumper_count = 5, target_count = 4;
struct Point { int x, y; uint32_t track_id; };
struct Tone { unsigned hz, ms; };
enum class Phase { Ready, Playing, GameOver };
struct Flipper { float px, py, rest, up, angle; bool on; };
struct State {
    float x = center + 96, y = center - 150, vx = -1.2f, vy = 0.6f;
    float obstacle_angle = 0;
    int points = 0, balls = 3;
    std::array<float, bumper_count> bumper_x{}, bumper_y{};
    std::array<float, target_count> target_x{}, target_y{};
    std::array<bool, target_count> target_up{};
    std::array<Flipper, 2> flippers{};
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
    bool input(bool valid, bool cancelled, uint32_t sequence, const std::vector<Point> &points);
    bool step(std::vector<Tone> &tones);
    bool substep(std::vector<Tone> &tones, const std::array<float, 2> &omega,
        std::array<bool, 2> &kicked);
    void lose_ball(std::vector<Tone> &tones);
    State state_;
    uint32_t accumulated_ms_ = 0, last_sequence_ = 0;
    bool have_sequence_ = false, wait_release_ = true, consume_touch_ = false;
};
}
