#include "espocket/mouse_model.hpp"
#include <algorithm>
#include <cmath>

namespace espocket::hid {
namespace {
constexpr float ring_inner = 152.0f;
constexpr float wheel_degrees = 18.0f;
constexpr float touch_gain = 1.8f;
constexpr float air_gain_x = 0.065f;
constexpr float air_gain_y = 0.085f;
constexpr float air_dead = 24.0f;
}

MouseModel::MouseModel() { reset(); }
void MouseModel::reset() { state_ = {}; cancel_input(); connected_ = false; have_reference_ = false; }
void MouseModel::cancel_input()
{
    have_sequence_ = false; active_ = false; moved_ = false; two_finger_ = false;
    state_.button_down = false; fraction_x_ = fraction_y_ = 0; ring_acc_ = 0;
}
void MouseModel::toggle_mode() { cancel_input(); state_.mode = state_.mode == Mode::trackpad ? Mode::air : Mode::trackpad; have_reference_ = false; }
void MouseModel::cycle_sensitivity() { state_.sensitivity = static_cast<uint8_t>((state_.sensitivity + 1) % 5); }
int MouseModel::clamp_report(int value) { return std::clamp(value, -127, 127); }
float MouseModel::angle(int x, int y) { return std::atan2(static_cast<float>(y - center), static_cast<float>(x - center)) * 57.2957795f; }

std::vector<MouseReport> MouseModel::finish_touch(bool had_motion, bool right_click)
{
    if (had_motion) return {};
    return {{static_cast<uint8_t>(right_click ? 2 : 1), 0, 0, 0}, {0, 0, 0, 0}};
}

std::vector<MouseReport> MouseModel::advance(uint32_t elapsed_ms, bool valid, bool cancelled,
    uint32_t sequence, const std::vector<Point> &points, std::optional<imu::Sample> sample)
{
    std::vector<MouseReport> reports;
    if (!connected_ || !valid || cancelled) { cancel_input(); return reports; }
    const bool fresh = !have_sequence_ || sequence != last_sequence_;
    if (!fresh) return reports;
    have_sequence_ = true; last_sequence_ = sequence;
    if (state_.mode == Mode::air && sample && sample->accel_valid) {
        if (!have_reference_) { reference_x_ = sample->accel_x_mg; reference_y_ = sample->accel_y_mg; have_reference_ = true; }
        float dx = (sample->accel_y_mg - reference_y_) * air_gain_x * elapsed_ms / 10.0f;
        float dy = (sample->accel_x_mg - reference_x_) * air_gain_y * elapsed_ms / 10.0f;
        if (std::fabs(dx) < air_dead) dx = 0; if (std::fabs(dy) < air_dead) dy = 0;
        const float gain = 0.55f + static_cast<float>(state_.sensitivity) * 0.3f;
        dx = dx * gain + fraction_x_; dy = dy * gain + fraction_y_;
        const int ix = clamp_report(static_cast<int>(dx)), iy = clamp_report(static_cast<int>(dy));
        fraction_x_ = dx - ix; fraction_y_ = dy - iy;
        if (ix || iy) reports.push_back({static_cast<uint8_t>(state_.button_down ? 1 : 0), ix, iy, 0});
    }
    if (points.empty()) {
        if (active_) { reports = finish_touch(moved_, two_finger_); active_ = false; state_.button_down = false; }
        return reports;
    }
    const auto &point = points.front();
    if (!active_) {
        active_ = true; active_track_ = point.track_id; last_x_ = point.x; last_y_ = point.y;
        last_angle_ = angle(point.x, point.y); moved_ = false; two_finger_ = points.size() > 1; ring_acc_ = 0;
        return reports;
    }
    if (points.size() > 1) { two_finger_ = true; }
    if (state_.mode == Mode::trackpad && !two_finger_) {
        const int dx = point.x - last_x_, dy = point.y - last_y_;
        const float radius = std::hypot(static_cast<float>(point.x - center), static_cast<float>(point.y - center));
        if (radius >= ring_inner) {
            float delta = angle(point.x, point.y) - last_angle_;
            while (delta > 180) delta -= 360; while (delta < -180) delta += 360;
            ring_acc_ += delta; while (ring_acc_ >= wheel_degrees) { ring_acc_ -= wheel_degrees; reports.push_back({0,0,0,-1}); }
            while (ring_acc_ <= -wheel_degrees) { ring_acc_ += wheel_degrees; reports.push_back({0,0,0,1}); }
            moved_ = moved_ || std::fabs(delta) > 0.5f;
        } else if (std::abs(dx) > 3 || std::abs(dy) > 3) {
            const float gain = touch_gain * (0.55f + static_cast<float>(state_.sensitivity) * 0.3f);
            reports.push_back({state_.button_down, static_cast<int>(dx * gain), static_cast<int>(dy * gain), 0}); moved_ = true;
        }
        last_angle_ = angle(point.x, point.y); last_x_ = point.x; last_y_ = point.y;
    }
    return reports;
}
} // namespace espocket::hid
