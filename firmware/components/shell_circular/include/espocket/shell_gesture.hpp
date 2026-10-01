#pragma once

#include <atomic>
#include <cstdint>

namespace espocket {

enum class ShellSurface : uint8_t {
    WatchFace,
    BatteryCard,
    BrightnessCard,
    QuickSettings,
    Launcher,
};

enum class GestureIntent : uint8_t {
    None,
    WatchFace,
    BatteryCard,
    BrightnessCard,
    QuickSettings,
    Launcher,
    Back,
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
};

struct ShellGestureState {
    std::atomic_bool consumed = false;
    std::atomic<ShellSurface> surface = ShellSurface::WatchFace;
    std::atomic<uint8_t> pending_gesture = 0;
    std::atomic<uint32_t> activity_generation = 0;
    // PROTOTYPE: Launcher pull-to-Home arbitration; Card support will use a separate contract.
    std::atomic<int32_t> launcher_scroll_top = 100000;
    std::atomic<int32_t> launcher_pull_distance = 0;
    std::atomic<int32_t> launcher_return_threshold = 100000;
    std::atomic_bool launcher_press_started_at_top = false;
};

void process_shell_gesture(ShellGestureState &state, const ShellGestureEvent &event,
                           const ShellGestureContext &context);

} // namespace espocket
