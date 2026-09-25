#include "esp_heap_caps.h"
#include "esp_log.h"
#include "espocket/system.hpp"

namespace {
constexpr char TAG[] = "ESPocket.System";
}

extern "C" void app_main()
{
    static espocket::System system;

    auto init_result = system.init();
    if (!init_result) {
        ESP_LOGE(TAG, "Fatal initialization failure: %s", init_result.error().c_str());
        return;
    }

    auto start_result = system.start();
    if (!start_result) {
        ESP_LOGE(TAG, "Fatal startup failure: %s", start_result.error().c_str());
        return;
    }

    ESP_LOGI(TAG, "ESPocket started");
    ESP_LOGI(
        TAG, "Heap internal free/largest: %zu/%zu; PSRAM free/largest: %zu/%zu",
        heap_caps_get_free_size(MALLOC_CAP_INTERNAL), heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL),
        heap_caps_get_free_size(MALLOC_CAP_SPIRAM), heap_caps_get_largest_free_block(MALLOC_CAP_SPIRAM)
    );
}
