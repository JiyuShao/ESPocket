#include "espocket/power_key_monitor.hpp"

#include <cinttypes>

#include "driver/gpio.h"
#include "esp_err.h"
#include "esp_log.h"

namespace espocket {
namespace {

constexpr char TAG[] = "ESPocket.PowerKey";
// On the 1.75C board, the PWR key's SYS_OUT signal is wired to GPIO3.
constexpr gpio_num_t PWR_GPIO = GPIO_NUM_3;
constexpr uint32_t POLL_MS = 40;
constexpr uint32_t DEBOUNCE_SAMPLES = 2;
constexpr uint32_t SHORT_PRESS_MAX_MS = 1000;

} // namespace

PowerKeyMonitor::~PowerKeyMonitor()
{
    stop();
}

std::expected<void, std::string> PowerKeyMonitor::start()
{
    if (running_.exchange(true, std::memory_order_acq_rel)) {
        return {};
    }

    pending_short_presses_.store(0, std::memory_order_release);

    const gpio_config_t config = {
        .pin_bit_mask = 1ULL << PWR_GPIO,
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    const auto result = gpio_config(&config);
    if (result != ESP_OK) {
        running_.store(false, std::memory_order_release);
        return std::unexpected("Failed to configure PWR GPIO3: " + std::string(esp_err_to_name(result)));
    }

    TaskHandle_t task = nullptr;
    if (xTaskCreate(task_entry, "ESPocketPwr", 3072, this, 5, &task) != pdPASS) {
        running_.store(false, std::memory_order_release);
        return std::unexpected("Failed to create PWR monitor task");
    }
    task_.store(task, std::memory_order_release);
    ESP_LOGI(TAG, "PWR monitor ready on GPIO3; BOOT remains reserved");
    return {};
}

void PowerKeyMonitor::stop()
{
    running_.store(false, std::memory_order_release);
    if (auto task = task_.load(std::memory_order_acquire); task != nullptr) {
        xTaskNotifyGive(task);
        for (int i = 0; i < 100 && task_.load(std::memory_order_acquire) != nullptr; ++i) {
            vTaskDelay(pdMS_TO_TICKS(10));
        }
    }
}

bool PowerKeyMonitor::take_short_press()
{
    return pending_short_presses_.exchange(0, std::memory_order_acq_rel) != 0;
}

void PowerKeyMonitor::task_entry(void *arg)
{
    static_cast<PowerKeyMonitor *>(arg)->run();
}

void PowerKeyMonitor::run()
{
    bool stable_pressed = false;
    bool candidate = false;
    uint32_t candidate_samples = 0;
    TickType_t pressed_at = 0;

    while (running_.load(std::memory_order_acquire)) {
        bool pressed = false;
        if (read_pressed(pressed)) {
            if (pressed == candidate) {
                ++candidate_samples;
            } else {
                candidate = pressed;
                candidate_samples = 1;
            }
            if (candidate_samples >= DEBOUNCE_SAMPLES && candidate != stable_pressed) {
                stable_pressed = candidate;
                if (stable_pressed) {
                    pressed_at = xTaskGetTickCount();
                } else {
                    const auto duration_ms = static_cast<uint32_t>(
                        (xTaskGetTickCount() - pressed_at) * portTICK_PERIOD_MS
                    );
                    if (duration_ms <= SHORT_PRESS_MAX_MS) {
                        pending_short_presses_.fetch_add(1, std::memory_order_acq_rel);
                        ESP_LOGI(TAG, "PWR short press duration=%" PRIu32 "ms", duration_ms);
                    } else {
                        ESP_LOGI(TAG, "PWR long press left to hardware duration=%" PRIu32 "ms", duration_ms);
                    }
                }
            }
        }
        ulTaskNotifyTake(pdTRUE, pdMS_TO_TICKS(POLL_MS));
    }

    task_.store(nullptr, std::memory_order_release);
    vTaskDelete(nullptr);
}

bool PowerKeyMonitor::read_pressed(bool &pressed)
{
    pressed = gpio_get_level(PWR_GPIO) != 0;
    return true;
}

} // namespace espocket
