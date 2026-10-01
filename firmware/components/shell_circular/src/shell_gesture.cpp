#include "espocket/shell_gesture.hpp"

#include <algorithm>

namespace espocket {

void process_shell_gesture(ShellGestureState &state, const ShellGestureEvent &event,
                           const ShellGestureContext &context)
{
    const auto exit_distance_px = state.launcher_return_threshold.load(std::memory_order_acquire);
    if (event.phase == ShellGesturePhase::Press) {
        state.consumed.store(false, std::memory_order_release);
        state.launcher_pull_distance.store(0, std::memory_order_release);
        state.launcher_press_started_at_top.store(
            state.surface.load(std::memory_order_acquire) == ShellSurface::Launcher &&
                state.launcher_scroll_top.load(std::memory_order_acquire) <= 1,
            std::memory_order_release
        );
        if (!context.display_on) {
            return;
        }
        state.activity_generation.fetch_add(1, std::memory_order_acq_rel);
        return;
    }
    if (event.phase == ShellGesturePhase::Release) {
        if ((!context.app_visible) &&
                state.surface.load(std::memory_order_acquire) == ShellSurface::Launcher &&
                state.launcher_press_started_at_top.load(std::memory_order_acquire) &&
                state.launcher_pull_distance.load(std::memory_order_acquire) >= exit_distance_px) {
            state.pending_gesture.store(
                static_cast<uint8_t>(GestureIntent::WatchFace), std::memory_order_release
            );
        } else {
            state.launcher_pull_distance.store(0, std::memory_order_release);
        }
        return;
    }
    if (event.phase != ShellGesturePhase::Pressing ||
            (!context.display_on)) {
        return;
    }

    const bool app_visible = context.app_visible;
    const auto surface = state.surface.load(std::memory_order_acquire);
    if (!app_visible && surface == ShellSurface::Launcher &&
            state.launcher_press_started_at_top.load(std::memory_order_acquire) &&
            event.direction == ShellGestureDirection::Down) {
        state.launcher_pull_distance.store(
            std::max<int32_t>(0, event.stop_y - event.start_y), std::memory_order_release
        );
        return; // Launcher commits Home on release only.
    }
    if (event.distance_px < exit_distance_px) {
        return;
    }

    GestureIntent intent = GestureIntent::None;
    const bool edge_back =
        (event.left_edge &&
         event.direction == ShellGestureDirection::Right) ||
        (event.right_edge &&
         event.direction == ShellGestureDirection::Left);
    if (app_visible && edge_back && context.edge_back_enabled) {
        intent = GestureIntent::Back;
    } else if (!app_visible) {
        switch (surface) {
        case ShellSurface::WatchFace:
            if (event.direction == ShellGestureDirection::Up) {
                intent = GestureIntent::Launcher;
            } else if (event.direction == ShellGestureDirection::Down) {
                intent = GestureIntent::QuickSettings;
            } else if (event.direction == ShellGestureDirection::Right) {
                intent = GestureIntent::BatteryCard;
            } else if (event.direction == ShellGestureDirection::Left) {
                intent = GestureIntent::BrightnessCard;
            }
            break;
        case ShellSurface::BatteryCard:
            if (event.direction == ShellGestureDirection::Left) {
                intent = GestureIntent::WatchFace;
            }
            break;
        case ShellSurface::BrightnessCard:
            if (event.direction == ShellGestureDirection::Right) {
                intent = GestureIntent::WatchFace;
            }
            break;
        case ShellSurface::QuickSettings:
            if (event.direction == ShellGestureDirection::Up) {
                intent = GestureIntent::WatchFace;
            }
            break;
        case ShellSurface::Launcher:
            break;
        }
    }
    if (intent == GestureIntent::None) {
        return;
    }

    bool expected = false;
    if (!state.consumed.compare_exchange_strong(
                expected,
                true,
                std::memory_order_acq_rel
            )) {
        return;
    }
    state.pending_gesture.store(static_cast<uint8_t>(intent), std::memory_order_release);
}

} // namespace espocket
