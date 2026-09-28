#pragma once

#include <atomic>
#include <cstdint>
#include <expected>
#include <string>

#include "driver/i2c_master.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

namespace espocket {

class PowerKeyMonitor {
public:
    PowerKeyMonitor() = default;
    ~PowerKeyMonitor();

    PowerKeyMonitor(const PowerKeyMonitor &) = delete;
    PowerKeyMonitor &operator=(const PowerKeyMonitor &) = delete;

    std::expected<void, std::string> start();
    void stop();
    uint32_t short_press_count() const;

private:
    static void task_entry(void *arg);
    void run();
    bool read_pressed(bool &pressed);

    i2c_master_dev_handle_t device_ = nullptr;
    std::atomic<TaskHandle_t> task_ = nullptr;
    std::atomic_bool running_ = false;
    std::atomic<uint32_t> short_press_count_ = 0;
};

} // namespace espocket
