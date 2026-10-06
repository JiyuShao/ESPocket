#pragma once

#include <memory>
#include <new>
#include <vector>

#include "espocket/shell_gesture.hpp"
#include "lvgl.h"

namespace espocket {

class PointerClickFilters {
public:
    bool install(ShellGestureState *gesture)
    try {
        remove();
        for (auto *input = lv_indev_get_next(nullptr); input != nullptr; input = lv_indev_get_next(input)) {
            if (lv_indev_get_type(input) != LV_INDEV_TYPE_POINTER) continue;
            auto state = std::make_unique<State>();
            state->input = input;
            state->gesture = gesture;
            state->read = lv_indev_get_read_cb(input);
            states_.push_back(std::move(state));
            const auto count = lv_indev_get_event_count(input);
            lv_indev_add_event_cb(input, filter_click, LV_EVENT_ALL, states_.back().get());
            if (lv_indev_get_event_count(input) != count + 1) {
                remove();
                return false;
            }
            lv_indev_set_read_cb(input, read_pointer);
        }
        return true;
    } catch (const std::bad_alloc &) {
        remove();
        return false;
    }

    void remove()
    {
        for (const auto &state : states_) {
            if (!state->input) continue;
            lv_indev_set_read_cb(state->input, state->read);
            lv_indev_remove_event_cb_with_user_data(state->input, filter_click, state.get());
        }
        states_.clear();
    }

private:
    struct State {
        lv_indev_t *input = nullptr;
        ShellGestureState *gesture = nullptr;
        lv_indev_read_cb_t read = nullptr;
        lv_point_t origin{};
        bool pressed = false;
        bool moved = false;
    };

    static void filter_click(lv_event_t *event)
    {
        auto *state = static_cast<State *>(lv_event_get_user_data(event));
        const auto code = lv_event_get_code(event);
        if (code == LV_EVENT_DELETE) {
            state->input = nullptr;
        } else if ((code == LV_EVENT_SHORT_CLICKED || code == LV_EVENT_CLICKED) &&
                   (state->moved || state->gesture->click_suppressed.load(std::memory_order_acquire))) {
            lv_indev_stop_processing(state->input);
        }
    }

    static void read_pointer(lv_indev_t *input, lv_indev_data_t *data)
    {
        for (uint32_t index = 0; index < lv_indev_get_event_count(input); ++index) {
            auto *descriptor = lv_indev_get_event_dsc(input, index);
            if (lv_event_dsc_get_cb(descriptor) != filter_click) continue;
            auto *state = static_cast<State *>(lv_event_dsc_get_user_data(descriptor));
            if (state->read) state->read(input, data);
            else data->state = LV_INDEV_STATE_RELEASED;
            const bool pressed = data->state == LV_INDEV_STATE_PRESSED;
            if (pressed && !state->pressed) {
                state->origin = data->point;
                state->moved = false;
            } else if (state->pressed) {
                const int64_t delta_x = static_cast<int64_t>(data->point.x) - state->origin.x;
                const int64_t delta_y = static_cast<int64_t>(data->point.y) - state->origin.y;
                state->moved |= delta_x * delta_x + delta_y * delta_y > 100;
            }
            state->pressed = pressed;
            return;
        }
        data->state = LV_INDEV_STATE_RELEASED;
    }

    std::vector<std::unique_ptr<State>> states_;
};

}
