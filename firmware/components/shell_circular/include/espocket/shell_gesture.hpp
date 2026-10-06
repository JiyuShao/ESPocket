#pragma once

#include <atomic>
#include <cstdint>
#include <mutex>

namespace espocket {

enum class ShellSurface : uint8_t {
    WatchFace,
    BatteryCard,
    BrightnessCard,
    QuickSettings,
    Launcher,
    LeftAppCard,
    RightAppCard,
};

enum class GestureIntent : uint8_t {
    None,
    WatchFace,
    BatteryCard,
    BrightnessCard,
    QuickSettings,
    Launcher,
    Back,
    LeftCardIn,
    RightCardIn,
    Consume,
};

enum class ShellGesturePhase { Press, Pressing, Release };
enum class ShellGestureDirection { None, Up, Down, Left, Right };

struct ShellGestureEvent {
    ShellGesturePhase phase = ShellGesturePhase::Press;
    ShellGestureDirection direction = ShellGestureDirection::None;
    bool left_edge = false;
    bool right_edge = false;
    int32_t start_y = 0;
    int32_t stop_y = 0;
    float distance_px = 0;
};

struct ShellGestureContext {
    bool display_on = true;
    bool app_visible = false;
    bool edge_back_enabled = false;
    bool edge_back_reserved = false;
};

struct ShellGestureState {
    std::mutex input_mutex;
    std::atomic_bool synthetic_input_active = false;
    std::atomic_bool consumed = false;
    std::atomic<ShellSurface> surface = ShellSurface::WatchFace;
    std::atomic<uint8_t> pending_gesture = 0;
    std::atomic<uint32_t> activity_generation = 0;
    std::atomic_bool modal_active = false;
    std::atomic_bool keyboard_active = false;
    // PROTOTYPE: Launcher pull-to-Home arbitration; Card support will use a separate contract.
    std::atomic<int32_t> launcher_scroll_top = 100000;
    std::atomic<int32_t> launcher_pull_distance = 0;
    std::atomic<int32_t> launcher_return_threshold = 100000;
    std::atomic_bool launcher_press_started_at_top = false;
};

struct ShellTouchGeometry {
    int32_t width = 0;
    int32_t horizontal_edge = 0;
    int32_t vertical_edge = 0;
    int32_t horizontal_threshold = 0;
    int32_t vertical_threshold = 0;
    float direction_tan = 1;
    bool direction_lock = true;
};

class ShellTouchTracker {
public:
    ShellTouchGeometry geometry;
    ShellGestureEvent sample(int32_t x, int32_t y, bool pressed, bool first);
private:
    int32_t start_x_ = 0;
    int32_t start_y_ = 0;
    ShellGestureDirection direction_ = ShellGestureDirection::None;
};

void reset_shell_gesture(ShellGestureState &state, bool discard_pending);
void process_shell_gesture(ShellGestureState &state, const ShellGestureEvent &event,
                           const ShellGestureContext &context);

} // namespace espocket
