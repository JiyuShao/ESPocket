// SPDX-License-Identifier: MIT
#pragma once
#include <array>
#include <atomic>
#include <cstdint>
#include <memory>
namespace espocket::water {
inline constexpr int center = 233, canvas_size = 466, bowl_radius = 222, particle_count = 380;
struct Impulse { float x = 0, y = 0, vx = 0, vy = 0, burst = 0; bool active = false; };
// The worker writes only a pool slot with no reader. A published frame is immutable.
struct Frame {
    Frame();
    static std::shared_ptr<Frame> create();
    std::array<uint16_t, canvas_size * canvas_size> pixels{};
    std::array<int16_t, canvas_size> previous_top{}, previous_bottom{};
    int boat_x0 = 1, boat_x1 = 0, boat_y0 = 1, boat_y1 = 0;
    int y0 = 0, y1 = canvas_size - 1;
};
struct Diagnostics {
    float boat_x = 0, boat_y = 0, energy = 0;
    int escaped = 0;
    bool finite = true, neighbor_overflow = false;
    uint64_t fingerprint = 14695981039346656037ULL;
};
// Worker-owned, with all solver/scratch storage allocated only while the App is open.
class Simulation {
public:
    Simulation() = default;
    ~Simulation();
    Simulation(const Simulation &) = delete;
    Simulation &operator=(const Simulation &) = delete;
    bool initialize();
    bool advance(unsigned elapsed_ms, const Impulse &, Frame &, const std::atomic_bool &cancelled);
    Diagnostics diagnostics() const;
private:
    struct State;
    State *state_ = nullptr;
};
}
