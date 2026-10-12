// Test candidate only. Runs outside System's Owner and USB adapter lifetime.
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "espocket/system.hpp"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <string_view>
#include <atomic>

namespace {
constexpr char TAG[] = "ReliabilityFixture";
std::atomic<unsigned> late_results{0};
struct Pending {
    esp_brookesia::system::core::AppId app;
    esp_brookesia::system::core::KeyboardRequestId keyboard;
    esp_brookesia::system::core::MessageDialogRequestId active, queued;
};
std::optional<Pending> enqueue_inputs(espocket::System &system)
{
    const auto app = system.get_active_app();
    if (!app) return std::nullopt;
    // App cleanup may legitimately report cancellation before the stop barrier.
    // Only a confirmed old result is forbidden; revoked() also checks rejection.
    auto keyboard = system.show_app_keyboard(app->app_id, {}, [](const auto &result) {
        if (result.confirmed) ++late_results;
    });
    esp_brookesia::system::core::MessageDialogOptions options;
    options.text = "Lifecycle fixture";
    options.buttons = {{"Close", esp_brookesia::system::core::MessageDialogButtonRole::Action}};
    auto active = system.show_system_message_dialog(options, [](const auto &) { ++late_results; });
    auto queued = system.show_system_message_dialog(options, [](const auto &) { ++late_results; });
    if (!keyboard || !active || !queued) { ESP_LOGE(TAG, "FAIL enqueue input"); return std::nullopt; }
    return Pending{app->app_id, *keyboard, *active, *queued};
}
bool revoked(espocket::System &system, const Pending &pending)
{
    if (system.complete_app_keyboard(pending.app, pending.keyboard, true, "late") ||
            system.hide_system_message_dialog(pending.active) ||
            system.hide_system_message_dialog(pending.queued) || late_results.load() != 0) {
        ESP_LOGE(TAG, "FAIL old input retained or delivered"); return false;
    }
    return true;
}
void sample(const char *phase, unsigned round)
{
    ESP_LOGI(TAG, "SAMPLE %s %u internal=%zu largest=%zu psram=%zu largest=%zu", phase, round,
             heap_caps_get_free_size(MALLOC_CAP_INTERNAL), heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL),
             heap_caps_get_free_size(MALLOC_CAP_SPIRAM), heap_caps_get_largest_free_block(MALLOC_CAP_SPIRAM));
}
bool exercise_apps(espocket::System &system)
{
    for (const auto id : {"espocket.app.hello", "espocket.app.hello_runtime"}) {
        bool found = false;
        for (const auto &app : system.list_apps()) {
            if (app.manifest.id != id) continue;
            found = true;
            if (auto result = system.start_app(app.app_id); !result) {
                ESP_LOGE(TAG, "FAIL start %s: %s", id, result.error().c_str());
                return false;
            }
            vTaskDelay(pdMS_TO_TICKS(250));
        }
        if (!found) { ESP_LOGE(TAG, "FAIL missing reference App %s", id); return false; }
    }
    return true;
}
bool stopped(espocket::System &system)
{
    using esp_brookesia::system::core::AppState;
    for (const auto &app : system.list_apps()) {
        if (app.state != AppState::Installed && app.state != AppState::Stopped) {
            ESP_LOGE(TAG, "FAIL retained App %s state=%d", app.manifest.id.c_str(), int(app.state));
            return false;
        }
    }
    return true;
}
} // namespace
extern "C" void app_main()
{
    static espocket::System system;
    constexpr std::string_view mode = "RELIABILITY_MODE";
    ESP_LOGW(TAG, "TEST ONLY mode=%s; do not use as ordinary firmware", mode.data());
    auto init = system.init();
    if (!init) {
        ESP_LOGE(TAG, "INIT_REJECTED %s", init.error().c_str());
        system.report_startup_failure(init.error());
        return; // Explicit hardware restart; never retry a failed startup in place.
    }
    auto start = system.start();
    if (!start) {
        ESP_LOGE(TAG, "START_REJECTED %s", start.error().c_str());
        system.report_startup_failure(start.error());
        return;
    }
    if (mode != "lifecycle") { ESP_LOGI(TAG, "OBSERVE_THEME_OR_FAILURE"); return; }
    sample("baseline", 0);
    for (unsigned round = 1; round <= 3; ++round) {
        if (!exercise_apps(system)) return;
        const auto pending = enqueue_inputs(system);
        if (!pending) return;
        system.stop();
        if (!stopped(system) || !revoked(system, *pending)) return;
        sample("stopped", round);
        if (auto result = system.start(); !result) {
            ESP_LOGE(TAG, "FAIL restart %u: %s", round, result.error().c_str()); return;
        }
        if (!revoked(system, *pending)) return;
        ESP_LOGI(TAG, "STOP_START_COMPLETE %u", round);
    }
    for (unsigned round = 1; round <= 3; ++round) {
        if (!exercise_apps(system)) return;
        const auto pending = enqueue_inputs(system);
        if (!pending) return;
        system.deinit();
        if (!revoked(system, *pending)) return;
        if (!system.list_apps().empty()) { ESP_LOGE(TAG, "FAIL retained registry"); return; }
        sample("deinitialized", round);
        if (auto result = system.init(); !result) {
            ESP_LOGE(TAG, "FAIL reinit %u: %s", round, result.error().c_str()); return;
        }
        if (auto result = system.start(); !result) {
            ESP_LOGE(TAG, "FAIL reinit start %u: %s", round, result.error().c_str()); return;
        }
        ESP_LOGI(TAG, "DEINIT_INIT_COMPLETE %u", round);
    }
    sample("final", 3);
    ESP_LOGI(TAG, "SEQUENCE_COMPLETE; heap samples and callback races require review");
}
