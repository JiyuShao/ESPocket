"""Exercise gesture classification through LVGL's real event dispatch boundary."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1]
ROOT = COMPONENT.parents[2]


class PointerClickFilterTest(unittest.TestCase):
    def test_drag_cannot_deliver_button_click(self):
        source = (ROOT / 'firmware/managed_components/lvgl__lvgl/src/indev/lv_indev.c').read_text()
        begin = source.index('static lv_result_t send_event(lv_event_code_t code, void * param)\n{')
        dispatch = source[begin:source.index('\nstatic void indev_scroll_throw_anim_cb', begin)]
        header = r'''
#pragma once
#include <cstdint>
#include <vector>
#include <algorithm>
enum lv_event_code_t { LV_EVENT_PRESSED, LV_EVENT_PRESSING, LV_EVENT_SHORT_CLICKED, LV_EVENT_CLICKED,
    LV_EVENT_RELEASED, LV_EVENT_LONG_PRESSED, LV_EVENT_LONG_PRESSED_REPEAT,
    LV_EVENT_ROTARY, LV_EVENT_KEY, LV_EVENT_DELETE, LV_EVENT_ALL };
enum lv_result_t { LV_RESULT_OK, LV_RESULT_INVALID };
struct lv_point_t { int32_t x = 0, y = 0; };
enum lv_indev_state_t { LV_INDEV_STATE_RELEASED, LV_INDEV_STATE_PRESSED };
constexpr int LV_INDEV_TYPE_POINTER = 1;
struct lv_indev_t;
struct lv_event_t { lv_event_code_t code; void *user_data; lv_indev_t *target; };
using lv_event_cb_t = void (*)(lv_event_t *);
struct lv_event_dsc_t { lv_event_cb_t callback; void *user_data; };
struct lv_indev_data_t { lv_point_t point; lv_indev_state_t state = LV_INDEV_STATE_RELEASED; };
using lv_indev_read_cb_t = void (*)(lv_indev_t *, lv_indev_data_t *);
struct lv_indev_t {
    bool stop_processing_query = false;
    lv_indev_data_t sample;
    lv_indev_read_cb_t read = nullptr;
    std::vector<lv_event_dsc_t> events;
};
inline std::vector<lv_indev_t *> inputs;
inline auto lv_event_get_code(lv_event_t *event) { return event->code; }
inline void *lv_event_get_user_data(lv_event_t *event) { return event->user_data; }
inline void lv_indev_stop_processing(lv_indev_t *input) { input->stop_processing_query = true; }
inline lv_indev_t *lv_indev_get_next(lv_indev_t *input) {
    if (!input) return inputs.empty() ? nullptr : inputs.front();
    auto next = std::find(inputs.begin(), inputs.end(), input) + 1;
    return next == inputs.end() ? nullptr : *next;
}
inline int lv_indev_get_type(lv_indev_t *) { return LV_INDEV_TYPE_POINTER; }
inline lv_indev_read_cb_t lv_indev_get_read_cb(lv_indev_t *input) { return input->read; }
inline void lv_indev_set_read_cb(lv_indev_t *input, lv_indev_read_cb_t read) { input->read = read; }
inline uint32_t lv_indev_get_event_count(lv_indev_t *input) { return input->events.size(); }
inline lv_event_dsc_t *lv_indev_get_event_dsc(lv_indev_t *input, uint32_t index) { return &input->events[index]; }
inline lv_event_cb_t lv_event_dsc_get_cb(lv_event_dsc_t *event) { return event->callback; }
inline void *lv_event_dsc_get_user_data(lv_event_dsc_t *event) { return event->user_data; }
inline void lv_indev_add_event_cb(lv_indev_t *input, lv_event_cb_t callback, lv_event_code_t, void *data) {
    input->events.push_back({callback, data});
}
inline uint32_t lv_indev_remove_event_cb_with_user_data(lv_indev_t *input, lv_event_cb_t callback, void *data) {
    return std::erase_if(input->events, [&](const auto &event) { return event.callback == callback && event.user_data == data; });
}
'''
        harness = r'''
#include <cassert>
#include "pointer_click_filter.hpp"
using namespace espocket;
ShellGestureState state;
lv_indev_t input;
lv_indev_t second_input;
lv_indev_t *indev_act = &input;
void *indev_obj_act = nullptr;
unsigned clicked = 0, released = 0;
bool indev_reset_check(lv_indev_t *) { return false; }
bool indev_stop_processing_check(lv_indev_t *device) { return device->stop_processing_query; }
void lv_indev_send_event(lv_indev_t *device, lv_event_code_t code, void *) {
    for (auto descriptor : device->events) {
        lv_event_t event{code, descriptor.user_data, device};
        descriptor.callback(&event);
    }
}
void read_sample(lv_indev_t *device, lv_indev_data_t *data) { *data = device->sample; }
void sample(lv_indev_t &device, int32_t x, int32_t y, bool pressed) {
    device.sample = {{x, y}, pressed ? LV_INDEV_STATE_PRESSED : LV_INDEV_STATE_RELEASED};
    lv_indev_data_t data;
    device.read(&device, &data);
    assert(data.point.x == x && data.point.y == y && data.state == device.sample.state);
}
void lv_obj_send_event(void *, lv_event_code_t code, void *) {
    if (code == LV_EVENT_CLICKED || code == LV_EVENT_SHORT_CLICKED) ++clicked;
    if (code == LV_EVENT_RELEASED) ++released;
}
''' + dispatch + r'''
int main() {
    inputs = {&input, &second_input};
    input.read = second_input.read = read_sample;
    PointerClickFilters filters;
    assert(filters.install(&state));
    state.launcher_return_threshold = 93;
    process_shell_gesture(state, {.phase = ShellGesturePhase::Press}, {});
    send_event(LV_EVENT_SHORT_CLICKED, nullptr);
    send_event(LV_EVENT_CLICKED, nullptr);
    assert(clicked == 2);
    const ShellGestureContext app{.app_visible = true, .edge_back_enabled = true};
    process_shell_gesture(state, {.phase = ShellGesturePhase::Press}, app);
    process_shell_gesture(state, {.phase = ShellGesturePhase::Pressing,
        .direction = ShellGestureDirection::Right, .left_edge = true, .distance_px = 120}, app);
    assert(state.pending_gesture == 0);
    send_event(LV_EVENT_SHORT_CLICKED, nullptr);
    send_event(LV_EVENT_CLICKED, nullptr);
    assert(clicked == 2);
    process_shell_gesture(state, {.phase = ShellGesturePhase::Release,
        .direction = ShellGestureDirection::Right, .left_edge = true, .distance_px = 120}, app);
    assert(state.pending_gesture == static_cast<uint8_t>(GestureIntent::Back));
    send_event(LV_EVENT_RELEASED, nullptr);
    send_event(LV_EVENT_CLICKED, nullptr);
    assert(clicked == 2 && released == 1);
    state.surface = ShellSurface::Launcher;
    process_shell_gesture(state, {.phase = ShellGesturePhase::Press}, {});
    process_shell_gesture(state, {.phase = ShellGesturePhase::Pressing,
        .direction = ShellGestureDirection::Up, .distance_px = 120}, {});
    send_event(LV_EVENT_CLICKED, nullptr);
    assert(clicked == 2);
    process_shell_gesture(state, {.phase = ShellGesturePhase::Press}, {});
    send_event(LV_EVENT_CLICKED, nullptr);
    assert(clicked == 3);
    state.modal_active = true;
    process_shell_gesture(state, {.phase = ShellGesturePhase::Press}, {});
    process_shell_gesture(state, {.phase = ShellGesturePhase::Release}, {});
    send_event(LV_EVENT_SHORT_CLICKED, nullptr);
    send_event(LV_EVENT_CLICKED, nullptr);
    assert(clicked == 5);
    assert(state.pending_gesture == 0);
    process_shell_gesture(state, {.phase = ShellGesturePhase::Press}, {});
    process_shell_gesture(state, {.phase = ShellGesturePhase::Pressing,
        .direction = ShellGestureDirection::Right, .distance_px = 120}, {});
    send_event(LV_EVENT_CLICKED, nullptr);
    assert(clicked == 5);
    state.click_suppressed = false;
    sample(input, 100, 100, true);
    send_event(LV_EVENT_PRESSED, nullptr);
    sample(input, 100, 80, true);
    send_event(LV_EVENT_PRESSING, nullptr);
    state.click_suppressed = false;
    sample(second_input, 200, 200, true);
    sample(input, 100, 100, false);
    send_event(LV_EVENT_RELEASED, nullptr);
    send_event(LV_EVENT_SHORT_CLICKED, nullptr);
    send_event(LV_EVENT_CLICKED, nullptr);
    assert(clicked == 5);
    sample(input, 100, 100, true);
    send_event(LV_EVENT_PRESSED, nullptr);
    sample(input, 100, 100, false);
    send_event(LV_EVENT_RELEASED, nullptr);
    send_event(LV_EVENT_CLICKED, nullptr);
    assert(clicked == 6);
    filters.remove();
    assert(input.read == read_sample && second_input.read == read_sample);
    assert(input.events.empty() && second_input.events.empty());
    assert(filters.install(&state));
    lv_indev_send_event(&second_input, LV_EVENT_DELETE, nullptr);
    filters.remove();
    assert(input.read == read_sample && input.events.empty());
}
'''
        with tempfile.TemporaryDirectory(prefix='espocket-pointer-click-') as temporary:
            directory = Path(temporary)
            (directory / 'lvgl.h').write_text(header)
            (directory / 'test.cpp').write_text(harness)
            binary = directory / 'test'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-I', str(directory),
                '-I', str(COMPONENT / 'include'), '-I', str(COMPONENT / 'src'),
                str(directory / 'test.cpp'), str(COMPONENT / 'src/shell_gesture.cpp'), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=5)
