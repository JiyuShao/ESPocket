#pragma once
// Included only by an explicitly prepared isolated test build.
#include <array>
#include <atomic>
#include "brookesia/service_manager.hpp"

namespace espocket::keyboard_isolation {
inline std::array<std::string, 2> manifests = {"KISO_NORMAL_ID", "KISO_FAILED_ID"};
inline std::array<esp_brookesia::system::core::AppId, 2> observers{};
inline esp_brookesia::system::core::AppId owner{};
inline esp_brookesia::service::EventSignalConnection connection;
inline std::atomic<bool> confirmed{false};
inline bool initialized = false;
inline unsigned round = 0;

inline void poll(System &system)
{
    if (!initialized) {
        const auto apps = system.list_apps();
        for (const auto &app : apps) {
            if (app.manifest.id == "espocket.app.hello_runtime") owner = app.app_id;
            for (unsigned i = 0; i < 2; ++i)
                if (app.manifest.id == manifests[i]) observers[i] = app.app_id;
        }
        if (!owner || !observers[0] || !observers[1]) return;
        auto service = esp_brookesia::service::ServiceManager::get_instance().get_service("SystemCore");
        if (!service) return;
        connection = service->subscribe_event("KeyboardClosed", [](const auto &, const auto &items) {
            const auto id = items.find("AppId");
            const auto ok = items.find("Confirmed");
            const auto text = items.find("Text");
            if (id == items.end() || ok == items.end() || text == items.end()) return;
            const auto *number = std::get_if<double>(&id->second);
            const auto *boolean = std::get_if<bool>(&ok->second);
            const auto *value = std::get_if<std::string>(&text->second);
            if (number && *number == owner && boolean && *boolean && value && *value == "KISO_PRIVATE_PROBE")
                confirmed.store(true, std::memory_order_release);
        });
        if (!connection.connected()) return;
        initialized = true;
        if (!system.start_app(observers[0])) ESP_LOGE("KISO", "KISO FIXTURE_ERROR observer_start");
        else ESP_LOGI("KISO", "KISO COORDINATOR_READY");
    }
    if (round >= 2 || !confirmed.exchange(false, std::memory_order_acq_rel)) return;
    const auto stopped = system.stop_app(observers[round]);
    if (bool(stopped) != (round == 0)) {
        ESP_LOGE("KISO", "KISO FIXTURE_ERROR stop_result");
        return;
    }
    auto app = system.get_app(observers[round]);
    using State = esp_brookesia::system::core::AppState;
    if (!app || (app->state != State::Stopped && app->state != State::Error)) {
        ESP_LOGE("KISO", "KISO FIXTURE_ERROR stopped_state");
        return;
    }
    const auto finished = round++;
    if (round == 1 && !system.start_app(observers[1]))
        ESP_LOGE("KISO", "KISO FIXTURE_ERROR failed_observer_start");
    // Starting a hidden fixture changes Core active_app_id; restore the
    // still-running visible Owner through the public lifecycle API.
    if (!system.resume_app(owner)) {
        ESP_LOGE("KISO", "KISO FIXTURE_ERROR owner_resume");
        return;
    }
    ESP_LOGI("KISO", "KISO STOP_COMPLETE %u", finished);
}
} // namespace espocket::keyboard_isolation
