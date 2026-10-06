#include "espocket/shell_gesture.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

namespace espocket {

void reset_shell_gesture(ShellGestureState &state, bool discard_pending)
{
    state.consumed.store(true, std::memory_order_release);
    state.click_suppressed.store(true, std::memory_order_release);
    state.pointer_cancel_pending.store(false, std::memory_order_release);
    state.launcher_press_started_at_top.store(false, std::memory_order_release);
    state.launcher_pull_distance.store(0, std::memory_order_release);
    if (discard_pending) { state.pending_gesture.store(0, std::memory_order_release); }
}

ShellGestureEvent ShellTouchTracker::sample(int32_t x, int32_t y, bool pressed, bool first)
{
    if (first) {
        start_x_ = x;
        start_y_ = y;
        direction_ = ShellGestureDirection::None;
    }
    const float dx = static_cast<float>(x) - start_x_;
    const float dy = static_cast<float>(y) - start_y_;
    const float tangent = dx == 0 ? std::numeric_limits<float>::infinity() : std::abs(dy / dx);
    auto direction = ShellGestureDirection::None;
    if (!first && tangent > geometry.direction_tan) {
        if (dy > geometry.vertical_threshold) { direction = ShellGestureDirection::Down; }
        if (dy < -geometry.vertical_threshold) { direction = ShellGestureDirection::Up; }
    } else if (!first) {
        if (dx > geometry.horizontal_threshold) { direction = ShellGestureDirection::Right; }
        if (dx < -geometry.horizontal_threshold) { direction = ShellGestureDirection::Left; }
    }
    if (direction != ShellGestureDirection::None &&
            (direction_ == ShellGestureDirection::None || !geometry.direction_lock)) {
        direction_ = direction;
    }
    return {
        .phase = first ? ShellGesturePhase::Press :
                 pressed ? ShellGesturePhase::Pressing : ShellGesturePhase::Release,
        .direction = direction_,
        .left_edge = start_x_ < geometry.horizontal_edge,
        .right_edge = geometry.width - start_x_ < geometry.horizontal_edge,
        .start_y = start_y_, .stop_y = y, .distance_px = std::hypot(dx, dy),
    };
}

void process_shell_gesture(ShellGestureState &state, const ShellGestureEvent &event,
                           const ShellGestureContext &context)
{
    if (event.phase == ShellGesturePhase::Press) {
        state.consumed.store(state.modal_active.load(std::memory_order_acquire), std::memory_order_release);
        state.click_suppressed.store(false, std::memory_order_release);
        state.pointer_cancel_pending.store(false, std::memory_order_release);
        state.launcher_pull_distance.store(0, std::memory_order_release);
        state.launcher_press_started_at_top.store(
            state.surface.load(std::memory_order_acquire) == ShellSurface::Launcher &&
                state.launcher_scroll_top.load(std::memory_order_acquire) <= 1,
            std::memory_order_release
        );
        if (!context.display_on) {
            reset_shell_gesture(state, true);
            return;
        }
        state.activity_generation.fetch_add(1, std::memory_order_acq_rel);
        if (state.modal_active.load(std::memory_order_acquire)) {
            state.pending_gesture.store(0, std::memory_order_release);
            state.launcher_press_started_at_top.store(false, std::memory_order_release);
        }
        return;
    }

    if (!context.display_on) {
        reset_shell_gesture(state, true);
        return;
    }
    if (event.distance_px > 10) {
        state.click_suppressed.store(true, std::memory_order_release);
    }
    if (state.modal_active.load(std::memory_order_acquire)) {
        state.consumed.store(true, std::memory_order_release);
        state.pending_gesture.store(0, std::memory_order_release);
        state.launcher_press_started_at_top.store(false, std::memory_order_release);
        state.launcher_pull_distance.store(0, std::memory_order_release);
        return;
    }

    if (state.consumed.load(std::memory_order_acquire)) {
        return;
    }
    const auto exit_distance_px = state.launcher_return_threshold.load(std::memory_order_acquire);
    if (state.keyboard_active.load(std::memory_order_acquire)) {
        const bool edge_back = (event.left_edge && event.direction == ShellGestureDirection::Right) ||
                               (event.right_edge && event.direction == ShellGestureDirection::Left);
        if (event.distance_px >= exit_distance_px && edge_back) {
            state.pointer_cancel_pending.store(true, std::memory_order_release);
            if (event.phase == ShellGesturePhase::Release &&
                    !state.consumed.exchange(true, std::memory_order_acq_rel)) {
                state.pending_gesture.store(static_cast<uint8_t>(GestureIntent::Back), std::memory_order_release);
            }
        }
        return;
    }
    if (event.phase == ShellGesturePhase::Pressing) {
        if (!context.app_visible &&
                state.surface.load(std::memory_order_acquire) == ShellSurface::Launcher &&
                state.launcher_press_started_at_top.load(std::memory_order_acquire) &&
                event.direction == ShellGestureDirection::Down) {
            state.launcher_pull_distance.store(
                std::max<int32_t>(0, event.stop_y - event.start_y), std::memory_order_release
            );
            if (state.launcher_pull_distance.load(std::memory_order_acquire) >= exit_distance_px) {
                state.pointer_cancel_pending.store(true, std::memory_order_release);
            }
            return;
        }
    }

    if (event.phase != ShellGesturePhase::Release && event.phase != ShellGesturePhase::Pressing) {
        return;
    }
    if (event.phase == ShellGesturePhase::Release && !context.app_visible &&
            state.surface.load(std::memory_order_acquire) == ShellSurface::Launcher &&
            state.launcher_press_started_at_top.load(std::memory_order_acquire) &&
            state.launcher_pull_distance.load(std::memory_order_acquire) >= exit_distance_px) {
        state.consumed.store(true, std::memory_order_release);
        state.pending_gesture.store(
            static_cast<uint8_t>(GestureIntent::WatchFace), std::memory_order_release
        );
        return;
    }
    if (event.phase == ShellGesturePhase::Release) {
        state.launcher_pull_distance.store(0, std::memory_order_release);
    }
    if (event.distance_px < exit_distance_px) { return; }

    const bool app_visible = context.app_visible;
    const auto surface = state.surface.load(std::memory_order_acquire);

    GestureIntent intent = GestureIntent::None;
    const bool edge_back =
        (event.left_edge &&
         event.direction == ShellGestureDirection::Right) ||
        (event.right_edge &&
         event.direction == ShellGestureDirection::Left);
    if (app_visible && edge_back && context.edge_back_enabled) {
        intent = GestureIntent::Back;
    } else if (app_visible && edge_back && context.edge_back_reserved) {
        intent = GestureIntent::Consume;
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
        case ShellSurface::LeftAppCard:
            if (event.direction == ShellGestureDirection::Left) intent = GestureIntent::LeftCardIn;
            else if (event.direction == ShellGestureDirection::Right) intent = GestureIntent::BatteryCard;
            break;
        case ShellSurface::RightAppCard:
            if (event.direction == ShellGestureDirection::Right) intent = GestureIntent::RightCardIn;
            else if (event.direction == ShellGestureDirection::Left) intent = GestureIntent::BrightnessCard;
            break;
        }
    }
    if (intent == GestureIntent::None) {
        return;
    }
    state.pointer_cancel_pending.store(true, std::memory_order_release);
    if (event.phase == ShellGesturePhase::Pressing) {
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
