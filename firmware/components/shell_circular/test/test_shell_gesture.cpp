#include <cassert>
#include <tuple>
#include <vector>
#include "espocket/shell_gesture.hpp"

using namespace espocket;

GestureIntent pending(const ShellGestureState &state)
{
    return static_cast<GestureIntent>(state.pending_gesture.load());
}

void press(ShellGestureState &state, ShellGestureContext context = {})
{
    process_shell_gesture(state, {.phase = ShellGesturePhase::Press}, context);
}

void move(ShellGestureState &state, ShellGestureDirection direction,
          ShellGestureContext context = {}, bool left = false, bool right = false,
          float distance = 120)
{
    process_shell_gesture(state, {
        .phase = ShellGesturePhase::Pressing, .direction = direction,
        .left_edge = left, .right_edge = right,
        .start_y = 100, .stop_y = 220, .distance_px = distance,
    }, context);
}

int main()
{
    const std::vector<std::tuple<ShellSurface, ShellGestureDirection, GestureIntent>> paths = {
        {ShellSurface::WatchFace, ShellGestureDirection::Up, GestureIntent::Launcher},
        {ShellSurface::WatchFace, ShellGestureDirection::Down, GestureIntent::QuickSettings},
        {ShellSurface::WatchFace, ShellGestureDirection::Left, GestureIntent::BrightnessCard},
        {ShellSurface::WatchFace, ShellGestureDirection::Right, GestureIntent::BatteryCard},
        {ShellSurface::QuickSettings, ShellGestureDirection::Up, GestureIntent::WatchFace},
        {ShellSurface::QuickSettings, ShellGestureDirection::Down, GestureIntent::None},
        {ShellSurface::BatteryCard, ShellGestureDirection::Left, GestureIntent::WatchFace},
        {ShellSurface::BatteryCard, ShellGestureDirection::Right, GestureIntent::None},
        {ShellSurface::BrightnessCard, ShellGestureDirection::Right, GestureIntent::WatchFace},
        {ShellSurface::BrightnessCard, ShellGestureDirection::Left, GestureIntent::None},
        {ShellSurface::LeftAppCard, ShellGestureDirection::Left, GestureIntent::LeftCardIn},
        {ShellSurface::LeftAppCard, ShellGestureDirection::Right, GestureIntent::BatteryCard},
        {ShellSurface::LeftAppCard, ShellGestureDirection::Up, GestureIntent::None},
        {ShellSurface::RightAppCard, ShellGestureDirection::Right, GestureIntent::RightCardIn},
        {ShellSurface::RightAppCard, ShellGestureDirection::Left, GestureIntent::BrightnessCard},
        {ShellSurface::RightAppCard, ShellGestureDirection::Down, GestureIntent::None},
    };
    for (const auto &[surface, direction, expected] : paths) {
        ShellGestureState state;
        state.surface = surface;
        state.launcher_return_threshold = 93;
        press(state);
        move(state, direction);
        assert(pending(state) == expected);
        assert(state.surface == surface); // The arbiter queues; it never navigates.
        assert(state.activity_generation == 1);
        move(state, ShellGestureDirection::Down);
        if (expected != GestureIntent::None) { assert(pending(state) == expected); }
    }

    ShellGestureState short_swipe;
    short_swipe.launcher_return_threshold = 93;
    press(short_swipe);
    move(short_swipe, ShellGestureDirection::Up, {}, false, false, 92);
    assert(pending(short_swipe) == GestureIntent::None);
    move(short_swipe, ShellGestureDirection::Up, {}, false, false, 93);
    assert(pending(short_swipe) == GestureIntent::Launcher);

    ShellGestureState asleep;
    asleep.launcher_return_threshold = 93;
    press(asleep, {.display_on = false});
    move(asleep, ShellGestureDirection::Up, {.display_on = false});
    assert(pending(asleep) == GestureIntent::None && asleep.activity_generation == 0);

    for (bool right_edge : {false, true}) {
        ShellGestureState app;
        app.launcher_return_threshold = 93;
        const auto direction = right_edge ? ShellGestureDirection::Left : ShellGestureDirection::Right;
        const ShellGestureContext root{.app_visible = true, .edge_back_enabled = false};
        press(app, root);
        move(app, direction, root, !right_edge, right_edge);
        assert(pending(app) == GestureIntent::None);
        const ShellGestureContext framework_root{.app_visible = true, .edge_back_reserved = true};
        press(app, framework_root);
        move(app, direction, framework_root, !right_edge, right_edge);
        assert(pending(app) == GestureIntent::Consume); // No Back, no click-through.
        assert(app.consumed);
        reset_shell_gesture(app, true);
        press(app, root); // AppOwned keeps its custom edge gesture.
        move(app, direction, root, !right_edge, right_edge);
        assert(pending(app) == GestureIntent::None);
        const ShellGestureContext detail{.app_visible = true, .edge_back_enabled = true};
        press(app, detail);
        move(app, direction, detail); // Normal horizontal App swipe is preserved.
        assert(pending(app) == GestureIntent::None);
        move(app, direction, detail, !right_edge, right_edge);
        assert(pending(app) == GestureIntent::Back);
    }

    for (bool starts_at_top : {false, true}) {
        ShellGestureState launcher;
        launcher.surface = ShellSurface::Launcher;
        launcher.launcher_return_threshold = 93;
        launcher.launcher_scroll_top = starts_at_top ? 0 : 200;
        press(launcher);
        move(launcher, ShellGestureDirection::Down);
        assert(pending(launcher) == GestureIntent::None);
        process_shell_gesture(launcher, {.phase = ShellGesturePhase::Release}, {});
        assert(pending(launcher) == (starts_at_top ? GestureIntent::WatchFace : GestureIntent::None));
        assert(launcher.surface == ShellSurface::Launcher);
    }
    ShellGestureState cancelled;
    cancelled.surface = ShellSurface::Launcher;
    cancelled.launcher_scroll_top = 0;
    cancelled.launcher_return_threshold = 93;
    press(cancelled);
    process_shell_gesture(cancelled, {
        .phase = ShellGesturePhase::Pressing, .direction = ShellGestureDirection::Down,
        .start_y = 100, .stop_y = 170, .distance_px = 70,
    }, {});
    process_shell_gesture(cancelled, {.phase = ShellGesturePhase::Release}, {});
    assert(pending(cancelled) == GestureIntent::None && cancelled.launcher_pull_distance == 0);
    // Cancelling an over-threshold pull must not manufacture the normal Release commit.
    press(cancelled);
    move(cancelled, ShellGestureDirection::Down);
    reset_shell_gesture(cancelled, true);
    process_shell_gesture(cancelled, {.phase = ShellGesturePhase::Release}, {});
    assert(pending(cancelled) == GestureIntent::None && cancelled.launcher_pull_distance == 0);
    cancelled.pending_gesture = static_cast<uint8_t>(GestureIntent::WatchFace);
    reset_shell_gesture(cancelled, false);
    assert(pending(cancelled) == GestureIntent::WatchFace);

    ShellGestureState modal;
    modal.surface = ShellSurface::Launcher;
    modal.launcher_scroll_top = 0;
    modal.launcher_return_threshold = 93;
    modal.modal_active = true;
    press(modal);
    move(modal, ShellGestureDirection::Down);
    process_shell_gesture(modal, {.phase = ShellGesturePhase::Release}, {});
    assert(pending(modal) == GestureIntent::None);
    move(modal, ShellGestureDirection::Right, {.app_visible = true, .edge_back_enabled = true}, true);
    assert(pending(modal) == GestureIntent::None);
    modal.modal_active = false;
    press(modal);
    move(modal, ShellGestureDirection::Down);
    process_shell_gesture(modal, {.phase = ShellGesturePhase::Release}, {});
    assert(pending(modal) == GestureIntent::WatchFace);

    ShellGestureState keyboard;
    keyboard.keyboard_active = true;
    keyboard.launcher_return_threshold = 93;
    for (const auto ctx : {ShellGestureContext{}, ShellGestureContext{.app_visible=true}}) {
        press(keyboard, ctx);
        move(keyboard, ShellGestureDirection::Up, ctx);
        assert(pending(keyboard) == GestureIntent::None);
        move(keyboard, ShellGestureDirection::Right, ctx, true);
        assert(pending(keyboard) == GestureIntent::Back);
        reset_shell_gesture(keyboard, true);
        keyboard.modal_active = true;
        press(keyboard, ctx);
        move(keyboard, ShellGestureDirection::Right, ctx, true);
        assert(pending(keyboard) == GestureIntent::None);
        keyboard.modal_active = false;
        press(keyboard, {.display_on=false, .app_visible=true});
        move(keyboard, ShellGestureDirection::Right, {.display_on=false, .app_visible=true}, true);
        assert(pending(keyboard) == GestureIntent::None);
    }

    ShellTouchTracker tracker;
    tracker.geometry = {.width = 466, .horizontal_edge = 27, .vertical_edge = 37,
                        .horizontal_threshold = 77, .vertical_threshold = 77};
    auto start = tracker.sample(10, 100, true, true);
    assert(start.phase == ShellGesturePhase::Press && start.left_edge && !start.right_edge);
    auto drag = tracker.sample(110, 100, true, false);
    assert(drag.phase == ShellGesturePhase::Pressing && drag.direction == ShellGestureDirection::Right &&
           drag.distance_px == 100);
    auto diagonal = tracker.sample(110, 300, true, false);
    assert(diagonal.direction == ShellGestureDirection::Right); // Direction locks like Display.
    auto release = tracker.sample(110, 300, false, false);
    assert(release.phase == ShellGesturePhase::Release && release.direction == diagonal.direction);
    assert(!tracker.sample(30, 300, true, true).left_edge);
    tracker.sample(200, 300, true, true);
    assert(tracker.sample(200, 223, true, false).direction == ShellGestureDirection::None);
    assert(tracker.sample(200, 222, true, false).direction == ShellGestureDirection::Up);
    tracker.sample(440, 100, true, true);
    assert(tracker.sample(300, 100, true, false).right_edge);

}
