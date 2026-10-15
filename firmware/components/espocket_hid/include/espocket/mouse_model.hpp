#pragma once

#include <cstdint>
#include <optional>
#include <vector>

#include "espocket/imu_source.hpp"
#include "espocket/mouse_endpoint.hpp"

namespace espocket::hid {

struct Point { int x = 0, y = 0, track_id = 0; };
enum class Mode { trackpad, air };

struct State {
    Mode mode = Mode::trackpad;
    bool imu_available = false;
    bool button_down = false;
    uint8_t sensitivity = 2;
};

class MouseModel {
public:
    static constexpr int center = 233;
    static constexpr int canvas_size = 466;

    MouseModel();
    void reset();
    void cancel_input();
    void set_imu_available(bool available) { state_.imu_available = available; }
    void set_connected(bool connected) { connected_ = connected; if (!connected) cancel_input(); }
    void toggle_mode();
    void cycle_sensitivity();
    const State &state() const { return state_; }

    std::vector<MouseReport> advance(uint32_t elapsed_ms, bool valid, bool cancelled,
        uint32_t sequence, const std::vector<Point> &points,
        std::optional<imu::Sample> sample = {});

private:
    static int clamp_report(int value);
    static float angle(int x, int y);
    std::vector<MouseReport> finish_touch(bool had_motion, bool right_click);
    State state_{};
    bool connected_ = false;
    bool have_sequence_ = false;
    uint32_t last_sequence_ = 0;
    bool active_ = false;
    bool moved_ = false;
    bool two_finger_ = false;
    int active_track_ = 0;
    int last_x_ = center, last_y_ = center;
    float last_angle_ = 0;
    float ring_acc_ = 0;
    bool have_reference_ = false;
    float reference_x_ = 0, reference_y_ = 0;
    float fraction_x_ = 0, fraction_y_ = 0;
};

} // namespace espocket::hid
