#include "espocket/power_key_monitor.hpp"

#include <cinttypes>

#include "esp_board_manager.h"
#include "esp_err.h"
#include "esp_log.h"

namespace espocket {
namespace {

constexpr char TAG[] = "ESPocket.PowerKey";
constexpr char I2C_PERIPHERAL[] = "i2c_master";
constexpr uint16_t TCA9554_ADDRESS = 0x20;
constexpr uint8_t TCA9554_INPUT_REGISTER = 0x00;
constexpr uint8_t TCA9554_CONFIG_REGISTER = 0x03;
constexpr uint8_t PWR_MASK = 1U << 4;
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

    void *bus = nullptr;
    auto result = esp_board_manager_get_periph_handle(I2C_PERIPHERAL, &bus);
    if (result != ESP_OK || bus == nullptr) {
        running_.store(false, std::memory_order_release);
        return std::unexpected("Board Manager I2C bus is unavailable");
    }

    const i2c_device_config_t config = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = TCA9554_ADDRESS,
        .scl_speed_hz = 400000,
        .scl_wait_us = 0,
        .flags = {.disable_ack_check = false},
    };
    result = i2c_master_bus_add_device(
                 static_cast<i2c_master_bus_handle_t>(bus),
                 &config,
                 &device_
             );
    if (result != ESP_OK) {
        running_.store(false, std::memory_order_release);
        return std::unexpected("Failed to attach TCA9554: " + std::string(esp_err_to_name(result)));
    }

    uint8_t direction = 0;
    result = i2c_master_transmit_receive(
                 device_, &TCA9554_CONFIG_REGISTER, 1, &direction, 1, 50
             );
    if (result == ESP_OK) {
        const uint8_t write[] = {TCA9554_CONFIG_REGISTER, static_cast<uint8_t>(direction | PWR_MASK)};
        result = i2c_master_transmit(device_, write, sizeof(write), 50);
    }
    if (result != ESP_OK) {
        i2c_master_bus_rm_device(device_);
        device_ = nullptr;
        running_.store(false, std::memory_order_release);
        return std::unexpected("Failed to configure PWR EXIO4: " + std::string(esp_err_to_name(result)));
    }

    TaskHandle_t task = nullptr;
    if (xTaskCreate(task_entry, "ESPocketPwr", 3072, this, 5, &task) != pdPASS) {
        i2c_master_bus_rm_device(device_);
        device_ = nullptr;
        running_.store(false, std::memory_order_release);
        return std::unexpected("Failed to create PWR monitor task");
    }
    task_.store(task, std::memory_order_release);
    ESP_LOGI(TAG, "PWR monitor ready on TCA9554 EXIO4; BOOT remains reserved");
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
    if (device_ != nullptr && task_.load(std::memory_order_acquire) == nullptr) {
        (void)i2c_master_bus_rm_device(device_);
        device_ = nullptr;
    }
}

uint32_t PowerKeyMonitor::short_press_count() const
{
    return short_press_count_.load(std::memory_order_acquire);
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
                        short_press_count_.fetch_add(1, std::memory_order_acq_rel);
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
    uint8_t level = 0;
    const auto result = i2c_master_transmit_receive(
                            device_, &TCA9554_INPUT_REGISTER, 1, &level, 1, 50
                        );
    if (result != ESP_OK) {
        ESP_LOGW(TAG, "PWR EXIO4 read failed: %s", esp_err_to_name(result));
        return false;
    }
    pressed = (level & PWR_MASK) != 0;
    return true;
}

} // namespace espocket
