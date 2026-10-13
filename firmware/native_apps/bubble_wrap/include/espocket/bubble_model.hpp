// Gameplay adapted from The-Badge app_games.c at the locked commit. MIT.
#pragma once
#include <array>
#include <cstdint>
#include <vector>
namespace espocket::bubble {
struct Point { int x, y; uint32_t track_id; };
struct Cell { int x, y; bool popped = false; };
struct Tone { unsigned hz, ms; };
class Model {
public:
    Model();
    void reset();
    void cancel_input();
    // elapsed_ms is active time only; cancelled input never supplies a release/click.
    std::vector<Tone> advance(uint32_t elapsed_ms, bool valid, bool cancelled,
                              uint32_t sequence, const std::vector<Point> &points);
    const std::vector<Cell> &cells() const { return cells_; }
    int remaining() const { return remaining_; }
private:
    struct Hold { uint32_t id; int x, y; uint32_t elapsed; bool background, refilled; };
    Tone refill();
    uint32_t random();
    std::vector<Cell> cells_;
    std::vector<Hold> holds_;
    uint32_t seed_ = 2463534242u, last_sequence_ = 0, refill_ms_ = 0;
    bool has_sequence_ = false;
    int remaining_ = 0;
};
}
