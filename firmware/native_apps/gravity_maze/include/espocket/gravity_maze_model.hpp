#pragma once

#include <cstdint>
#include <optional>
#include <vector>

#include "espocket/imu_source.hpp"

namespace espocket::gravity_maze {

struct Point { int x = 0, y = 0, track_id = 0; };

struct State {
    float marble_x = 233, marble_y = 233;
    float hole_x = 233, hole_y = 233;
    float velocity_x = 0, velocity_y = 0;
    uint32_t score = 0;
    bool imu_available = false;
};

class Model {
public:
    static constexpr int canvas_size = 466;
    static constexpr int center = 233;
    static constexpr float rim_radius = 201.0f;

    Model();
    void reset();
    void set_imu_available(bool available) { state_.imu_available = available; }
    const State &state() const { return state_; }
    void cancel_input();
    // A touch point is an explicit fallback control, never an injected IMU sample.
    void advance(uint32_t elapsed_ms, bool valid, bool cancelled, uint32_t sequence,
                 const std::vector<Point> &points, std::optional<imu::Sample> sample = {});

private:
    uint32_t random();
    void new_hole();
    State state_{};
    uint32_t seed_ = 0xA341316Cu;
    uint32_t last_sequence_ = 0;
    bool have_sequence_ = false;
    bool wait_release_ = true;
    bool have_reference_ = false;
    float reference_x_ = 0, reference_y_ = 0;
};

} // namespace espocket::gravity_maze
