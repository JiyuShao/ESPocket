#pragma once

#include "espocket/system.hpp"

#include <algorithm>
#include <cinttypes>
#include <utility>
#include <vector>

#include "sdkconfig.h"

#include "boost/json/array.hpp"
#include "boost/json/value.hpp"
#include "brookesia/app_settings.hpp"
#include "brookesia/app_store.hpp"
#include "brookesia/gui_lvgl.hpp"
#include "brookesia/lib_utils/describe_helpers.hpp"
#if CONFIG_ESPOCKET_M2_LIFECYCLE_STRESS
#include "brookesia/lib_utils/memory_profiler.hpp"
#endif
#include "brookesia/service_helper/media/display.hpp"
#include "brookesia/service_manager/helper/base.hpp"
#if CONFIG_ESPOCKET_M6_RESOURCE_TRACE
#include "esp_heap_caps.h"
#endif
#include "esp_app_desc.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "espocket/circular_shell.hpp"
#include "espocket/developer_mode.hpp"
#include "espocket/hello_app.hpp"
#include "espocket/interaction_test_adapter.hpp"
#include "espocket/page_navigator.hpp"
#include "espocket/settings_navigation_adapter.hpp"
#include "espocket/power_key_monitor.hpp"

namespace espocket {
namespace {

constexpr char TAG[] = "ESPocket.System";
constexpr uint32_t DISPLAY_TIMEOUT_MS = 1000;

using DisplayHelper = esp_brookesia::service::helper::Display;
using DisplaySource = esp_brookesia::gui::lvgl::DisplaySource;

#if CONFIG_ESPOCKET_M2_LIFECYCLE_STRESS
constexpr size_t M2_STRESS_CYCLES = 50;

inline std::expected<void, std::string> run_m2_lifecycle_stress(
    esp_brookesia::system::core::System &system,
    esp_brookesia::system::core::AppId app_id
)
{
    using AppState = esp_brookesia::system::core::AppState;
    using MemoryProfiler = esp_brookesia::lib_utils::MemoryProfiler;

    ESP_LOGI(TAG, "M2_STRESS BEGIN cycles=%zu app_id=%" PRIu32, M2_STRESS_CYCLES, app_id);
    for (size_t cycle = 1; cycle <= M2_STRESS_CYCLES; ++cycle) {
        const auto expected_state = cycle == 1 ? AppState::Installed : AppState::Stopped;
        auto before_start = system.get_app(app_id);
        if (!before_start.has_value() || before_start->state != expected_state) {
            ESP_LOGE(TAG, "M2_STRESS FAIL cycle=%zu phase=pre_start_state", cycle);
            return std::unexpected("M2 lifecycle stress has an invalid pre-start state at cycle " + std::to_string(cycle));
        }

        auto start_result = system.start_app(app_id);
        if (!start_result) {
            ESP_LOGE(TAG, "M2_STRESS FAIL cycle=%zu phase=start error=%s", cycle, start_result.error().c_str());
            return std::unexpected("M2 lifecycle stress start failed at cycle " + std::to_string(cycle));
        }

        auto running = system.get_app(app_id);
        if (!running.has_value() || running->state != AppState::Running) {
            ESP_LOGE(TAG, "M2_STRESS FAIL cycle=%zu phase=running_state", cycle);
            auto cleanup_result = system.stop_app(app_id);
            if (!cleanup_result) {
                ESP_LOGE(TAG, "M2_STRESS cleanup failed: %s", cleanup_result.error().c_str());
            }
            return std::unexpected("M2 lifecycle stress did not reach Running at cycle " + std::to_string(cycle));
        }

        auto stop_result = system.stop_app(app_id);
        if (!stop_result) {
            ESP_LOGE(TAG, "M2_STRESS FAIL cycle=%zu phase=stop error=%s", cycle, stop_result.error().c_str());
            return std::unexpected("M2 lifecycle stress stop failed at cycle " + std::to_string(cycle));
        }

        auto stopped = system.get_app(app_id);
        if (!stopped.has_value() || stopped->state != AppState::Stopped) {
            ESP_LOGE(TAG, "M2_STRESS FAIL cycle=%zu phase=stopped_state", cycle);
            return std::unexpected("M2 lifecycle stress did not reach Stopped at cycle " + std::to_string(cycle));
        }

        auto gui_probe = system.gui_set_text(app_id, "/hello/counter", "cleanup probe");
        if (gui_probe || gui_probe.error() != "App GUI document is not loaded") {
            ESP_LOGE(TAG, "M2_STRESS FAIL cycle=%zu phase=gui_cleanup", cycle);
            return std::unexpected("M2 lifecycle stress GUI cleanup failed at cycle " + std::to_string(cycle));
        }

        const auto heap = MemoryProfiler::take_raw_heap_snapshot();
        if (!heap.valid || heap.internal_free == 0 || heap.external_free == 0 ||
                heap.internal_largest == 0 || heap.external_largest == 0) {
            ESP_LOGE(TAG, "M2_STRESS FAIL cycle=%zu phase=heap_snapshot", cycle);
            return std::unexpected("M2 lifecycle stress heap snapshot failed at cycle " + std::to_string(cycle));
        }

        ESP_LOGI(
            TAG,
            "M2_STRESS CYCLE cycle=%zu start=Running stop=Stopped gui=Unloaded internal_free=%zu psram_free=%zu "
            "internal_largest=%zu psram_largest=%zu",
            cycle,
            heap.internal_free,
            heap.external_free,
            heap.internal_largest,
            heap.external_largest
        );
    }

    ESP_LOGI(TAG, "M2_STRESS COMPLETE cycles=%zu", M2_STRESS_CYCLES);
    return {};
}
#endif

} // namespace


} // namespace espocket
