#pragma once

#include "espocket/circular_shell.hpp"
#include <algorithm>
#include <array>
#include <cinttypes>
#include <utility>
#include "esp_log.h"
#include "esp_lv_adapter.h"
#include "esp_timer.h"
#include "lvgl.h"
#include "sdkconfig.h"
#ifndef CONFIG_ESPOCKET_M6_SCREEN_TIMEOUT_SECONDS
#define CONFIG_ESPOCKET_M6_SCREEN_TIMEOUT_SECONDS 30
#endif

namespace espocket {
namespace {
constexpr char SHELL_TAG[] = "ESPocket.Shell";
constexpr std::string_view PAGE_FLOW = "shell_pages";
constexpr std::string_view LAUNCHER_PULL_PATH = "/launcher/pull_hint";
constexpr std::string_view HOME_INTENT_TIMER = "espocket.home_intent";
constexpr int HOME_INTENT_INTERVAL_MS = 50;
constexpr std::string_view STATUS_TIMER = "espocket.status";
constexpr int STATUS_INTERVAL_MS = 30'000;
constexpr int64_t SCREEN_TIMEOUT_US =
    static_cast<int64_t>(CONFIG_ESPOCKET_M6_SCREEN_TIMEOUT_SECONDS) * 1'000'000;

class LvglLock {
public:
    LvglLock()
        : locked_(esp_lv_adapter_lock(-1) == ESP_OK)
    {}

    ~LvglLock()
    {
        if (locked_) {
            esp_lv_adapter_unlock();
        }
    }

    explicit operator bool() const
    {
        return locked_;
    }

private:
    bool locked_ = false;
};

inline lv_keyboard_mode_t keyboard_mode(std::string_view mode)
{
    if (mode == "number") {
        return LV_KEYBOARD_MODE_NUMBER;
    }
    if (mode == "special") {
        return LV_KEYBOARD_MODE_SPECIAL;
    }
    if (mode == "upper") {
        return LV_KEYBOARD_MODE_TEXT_UPPER;
    }
    return LV_KEYBOARD_MODE_TEXT_LOWER;
}

constexpr std::array<std::string_view, 4> KEYBOARD_MODES = {
    "text", "upper", "number", "special"
};

template <typename Modes>
constexpr bool supports_keyboard_modes(const Modes &allowed_modes)
{
    return allowed_modes.empty() ||
           (allowed_modes.size() == KEYBOARD_MODES.size() &&
            std::ranges::all_of(KEYBOARD_MODES, [&allowed_modes](std::string_view mode) {
                return std::ranges::find(allowed_modes, mode) != allowed_modes.end();
            }));
}

static_assert(supports_keyboard_modes(KEYBOARD_MODES));
static_assert(!supports_keyboard_modes(std::array<std::string_view, 1>{"text"}));

// LVGL owns this reference until deletion, including a failed stop/hide.
// Invalidated states reject input; callback userdata cannot outlive its storage.
template<class State>
void retain_overlay_userdata(lv_obj_t *overlay, const std::shared_ptr<State> &state)
{
    auto *retained = new std::shared_ptr<State>(state);
    lv_obj_add_event_cb(overlay, [](lv_event_t *event) {
        if (lv_event_get_target(event) != lv_event_get_current_target(event)) return;
        delete static_cast<std::shared_ptr<State> *>(lv_event_get_user_data(event));
    }, LV_EVENT_DELETE, retained);
}

} // namespace

struct CircularShell::LoadingState {
    std::mutex mutex;
    bool startup = false;
    bool app_wait = false;
    esp_brookesia::system::core::AppId app_id = esp_brookesia::system::core::INVALID_APP_ID;
    lv_obj_t *overlay = nullptr;
    bool invalidated = false;
};

struct CircularShell::KeyboardState {
    std::mutex mutex;
    esp_brookesia::system::core::AppId app_id =
        esp_brookesia::system::core::INVALID_APP_ID;
    esp_brookesia::system::core::KeyboardRequestId request_id =
        esp_brookesia::system::core::INVALID_KEYBOARD_REQUEST_ID;
    lv_obj_t *overlay = nullptr;
    lv_obj_t *text_area = nullptr;
    bool result_pending = false;
    bool confirmed = false;
    bool suspended = false;
    bool invalidated = false;
    std::string text;
};

struct CircularShell::MessageDialogState {
    bool suspended = false;
    std::mutex mutex;
    esp_brookesia::system::core::AppId app_id = esp_brookesia::system::core::INVALID_APP_ID;
    esp_brookesia::system::core::MessageDialogRequestId request_id =
        esp_brookesia::system::core::INVALID_MESSAGE_DIALOG_REQUEST_ID;
    lv_obj_t *overlay = nullptr;
    bool result_pending = false;
    int32_t button_index = -1;
    int64_t deadline_us = 0;
    int64_t paused_at_us = -1;
    bool invalidated = false;
    struct Button { MessageDialogState *state; int32_t index; };
    std::array<Button, 3> buttons{{{this, 0}, {this, 1}, {this, 2}}};
};

struct CircularShell::BackOverlayState {
    lv_obj_t *button = nullptr;
    lv_obj_t *card_hint = nullptr;
    std::atomic_bool clicked = false;
};


} // namespace espocket
