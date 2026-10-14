// SPDX-License-Identifier: MIT
#pragma once
#include <array>
#include <atomic>
#include <cstdint>
#include <memory>
namespace espocket::orbit {
inline constexpr int canvas_size = 466, center = 233, radius = 206;
enum class Kind { Moon, Earth, Sun, Jupiter };
struct Attitude { float longitude = 0, tilt = 0, lean = 0; bool moving = false; };
struct Touch { enum class Phase { None, Press, Move, Release, Cancel }; Phase phase = Phase::None; int x = 0, y = 0; };
class Motion {
public:
    void reset();
    void cancel_touch();
    void request_redraw() { dirty_ = true; }
    bool advance(unsigned elapsed_ms, Touch);
    Attitude attitude() const;
private:
    float longitude_ = 0, spin_ = 0.1f, tilt_ = 0, tilt_velocity_ = 0, lean_ = 0, lean_velocity_ = 0;
    int drag_x_ = 0, drag_y_ = 0;
    bool dragging_ = false, dirty_ = true, was_moving_ = false;
};
struct Frame {
    std::array<uint16_t, canvas_size * canvas_size> pixels{};
    static std::shared_ptr<Frame> create();
};
// Worker-only renderer, with texture/depth/shading/UV tables in one checked PSRAM allocation.
class Renderer {
public:
    Renderer() = default;
    ~Renderer();
    Renderer(const Renderer &) = delete;
    Renderer &operator=(const Renderer &) = delete;
    bool initialize(Kind);
    bool paint(Attitude, Frame &, const std::atomic_bool &cancelled);
private:
    struct State;
    State *state_ = nullptr;
};
}
