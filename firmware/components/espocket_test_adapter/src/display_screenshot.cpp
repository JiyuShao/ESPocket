#include "espocket/screenshot.hpp"

#include <array>
#include <algorithm>
#include <new>
#include <vector>

#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_lv_adapter.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "sdkconfig.h"
#include "lvgl.h"
#include "src/core/lv_global.h"
#include "src/misc/cache/lv_cache.h"
#include "src/misc/cache/instance/lv_image_cache.h"
#include "psa/crypto.h"

namespace espocket {
namespace {
void capture_flush(lv_event_t *event)
{
    auto *assembly = static_cast<ScreenshotAssembly *>(lv_event_get_user_data(event));
    auto *display = static_cast<lv_display_t *>(lv_event_get_target(event));
    const auto *area = static_cast<const lv_area_t *>(lv_event_get_param(event));
    const auto *buffer = lv_display_get_buf_active(display);
    if (!area || !buffer || !buffer->data) {
        (void)assembly->append(-1, -1, -1, -1, {}, 0);
        return;
    }
    try {
        (void)assembly->append(area->x1, area->y1, area->x2, area->y2,
                              {buffer->data, buffer->data_size}, buffer->header.stride);
    } catch (const std::bad_alloc &) {
        (void)assembly->append(-1, -1, -1, -1, {}, 0);
    }
}
} // namespace

std::expected<TestScreenshot, std::string> capture_display_screenshot()
try
{
    // The developer USB task normally runs below both GUI contenders. Match
    // their priority only for this synchronous capture so repeated higher
    // priority GUI work cannot reacquire the mutex ahead of it indefinitely.
    // Never lower an already higher caller; restore even on lock timeout.
    struct CapturePriority {
        UBaseType_t previous = uxTaskPriorityGet(nullptr);
        CapturePriority() {
            vTaskPrioritySet(nullptr, std::max(previous, static_cast<UBaseType_t>(
                std::max(CONFIG_BROOKESIA_SYSTEM_CORE_WORKER_PRIORITY,
                         CONFIG_BROOKESIA_GUI_LVGL_DISPLAY_SOURCE_TASK_PRIORITY))));
        }
        ~CapturePriority() { vTaskPrioritySet(nullptr, previous); }
    } capture_priority;
    // A synchronous refresh under the existing LVGL lock includes bottom, App,
    // top and system layers. Observe FLUSH_START without replacing the HAL callback.
    if (esp_lv_adapter_lock(2000) != ESP_OK) return std::unexpected("busy");
    struct Unlock { ~Unlock() { esp_lv_adapter_unlock(); } } unlock;
    auto *display = lv_display_get_default();
    if (!display || lv_display_get_color_format(display) != LV_COLOR_FORMAT_RGB565 ||
            lv_display_get_render_mode(display) != LV_DISPLAY_RENDER_MODE_PARTIAL ||
            lv_display_get_rotation(display) != LV_DISPLAY_ROTATION_0 ||
            lv_display_get_offset_x(display) != 0 || lv_display_get_offset_y(display) != 0) {
        return std::unexpected("unsupported");
    }
    const auto width = lv_display_get_horizontal_resolution(display);
    const auto height = lv_display_get_vertical_resolution(display);
    if (width <= 0 || height <= 0 || width > 1024 || height > 1024)
        return std::unexpected("unsupported");
    // Reserve the screenshot peak before allocating it, and keep the synchronous
    // refresh from repopulating decoded images while the frame is being assembled.
    // Restore under the same LVGL lock on every exit, including allocation errors.
    struct PauseImageCache {
        uint32_t budget = static_cast<uint32_t>(
            lv_cache_get_max_size(LV_GLOBAL_DEFAULT()->img_cache, nullptr));
        PauseImageCache() {
            lv_image_cache_drop(nullptr);
            lv_image_cache_resize(0, true);
        }
        ~PauseImageCache() { lv_image_cache_resize(budget, false); }
    } pause_image_cache;
    const size_t size = static_cast<size_t>(width) * height * 2;
    auto pixels = std::make_shared<ScreenshotPixels>(width, height, [](size_t bytes) {
        auto *data = static_cast<uint8_t *>(heap_caps_malloc(bytes, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
        if (!data) ESP_LOGW("ESPocket.Screenshot", "Row allocation failed: need=%u free=%u largest=%u",
                           static_cast<unsigned>(bytes),
                           static_cast<unsigned>(heap_caps_get_free_size(MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT)),
                           static_cast<unsigned>(heap_caps_get_largest_free_block(MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT)));
        return std::shared_ptr<uint8_t>(data, heap_caps_free);
    });
    TestScreenshot frame{static_cast<uint32_t>(width), static_cast<uint32_t>(height), size,
                         pixels, {}};
    std::vector<uint8_t> coverage((static_cast<size_t>(width) * height + 7) / 8);
    ScreenshotAssembly assembly(frame.width, frame.height, *pixels, coverage);
    const auto event_count = lv_display_get_event_count(display);
    lv_display_add_event_cb(display, capture_flush, LV_EVENT_FLUSH_START, &assembly);
    if (lv_display_get_event_count(display) != event_count + 1) return std::unexpected("internal");
    lv_obj_invalidate(lv_display_get_screen_active(display));
    lv_refr_now(display);
    lv_display_remove_event_cb_with_user_data(display, capture_flush, &assembly);
    if (!assembly.complete()) return std::unexpected("incomplete_frame");
    std::array<unsigned char, 32> hash{};
    size_t hash_size = 0;
    psa_hash_operation_t operation = PSA_HASH_OPERATION_INIT;
    struct AbortHash { psa_hash_operation_t &operation; ~AbortHash() { psa_hash_abort(&operation); } } abort_hash{operation};
    if (psa_crypto_init() != PSA_SUCCESS || psa_hash_setup(&operation, PSA_ALG_SHA_256) != PSA_SUCCESS)
        return std::unexpected("internal");
    std::array<uint8_t, 2048> row;
    const size_t row_bytes = static_cast<size_t>(width) * 2;
    for (size_t offset = 0; offset < size; offset += row_bytes) {
        if (!pixels->read(offset, std::span(row).first(row_bytes)) ||
                psa_hash_update(&operation, row.data(), row_bytes) != PSA_SUCCESS)
            return std::unexpected("internal");
    }
    if (psa_hash_finish(&operation, hash.data(), hash.size(), &hash_size) != PSA_SUCCESS || hash_size != hash.size())
        return std::unexpected("internal");
    constexpr char hex[] = "0123456789abcdef";
    frame.sha256.reserve(64);
    for (auto byte : hash) { frame.sha256 += hex[byte >> 4]; frame.sha256 += hex[byte & 15]; }
    ESP_LOGI("ESPocket.Screenshot", "Capture complete: rgb565=%u stored=%u; caller minimum free stack: %u bytes",
             static_cast<unsigned>(size), static_cast<unsigned>(pixels->stored_size()),
             static_cast<unsigned>(uxTaskGetStackHighWaterMark(nullptr)));
    return frame;
}
catch (const std::bad_alloc &) { return std::unexpected("internal"); }

} // namespace espocket
