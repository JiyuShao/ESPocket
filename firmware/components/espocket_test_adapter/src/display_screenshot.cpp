#include "espocket/screenshot.hpp"

#include <array>
#include <new>
#include <vector>

#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_lv_adapter.h"
#include "lvgl.h"
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
    (void)assembly->append(area->x1, area->y1, area->x2, area->y2,
                          {buffer->data, buffer->data_size}, buffer->header.stride);
}
} // namespace

std::expected<TestScreenshot, std::string> capture_display_screenshot()
try
{
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
    const size_t size = static_cast<size_t>(width) * height * 2;
    auto *pixels = static_cast<uint8_t *>(heap_caps_malloc(size, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
    if (!pixels) return std::unexpected("internal");
    TestScreenshot frame{static_cast<uint32_t>(width), static_cast<uint32_t>(height), size,
                         std::shared_ptr<uint8_t>(pixels, heap_caps_free), {}};
    std::vector<uint8_t> coverage((static_cast<size_t>(width) * height + 7) / 8);
    ScreenshotAssembly assembly(frame.width, frame.height, {pixels, size}, coverage);
    const auto event_count = lv_display_get_event_count(display);
    lv_display_add_event_cb(display, capture_flush, LV_EVENT_FLUSH_START, &assembly);
    if (lv_display_get_event_count(display) != event_count + 1) return std::unexpected("internal");
    lv_obj_invalidate(lv_display_get_screen_active(display));
    lv_refr_now(display);
    lv_display_remove_event_cb_with_user_data(display, capture_flush, &assembly);
    if (!assembly.complete()) return std::unexpected("incomplete_frame");
    std::array<unsigned char, 32> hash{};
    size_t hash_size = 0;
    if (psa_crypto_init() != PSA_SUCCESS ||
            psa_hash_compute(PSA_ALG_SHA_256, pixels, size, hash.data(), hash.size(), &hash_size) != PSA_SUCCESS ||
            hash_size != hash.size()) return std::unexpected("internal");
    constexpr char hex[] = "0123456789abcdef";
    frame.sha256.reserve(64);
    for (auto byte : hash) { frame.sha256 += hex[byte >> 4]; frame.sha256 += hex[byte & 15]; }
    ESP_LOGI("ESPocket.Screenshot", "Capture complete; caller minimum free stack: %u bytes",
             static_cast<unsigned>(uxTaskGetStackHighWaterMark(nullptr)));
    return frame;
}
catch (const std::bad_alloc &) { return std::unexpected("internal"); }

} // namespace espocket
