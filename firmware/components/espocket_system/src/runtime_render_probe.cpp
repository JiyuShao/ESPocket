#include "runtime_render_probe.hpp"
#include <algorithm>
#include <cstring>
#include <cstdio>
#include "sdkconfig.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_lv_adapter.h"
#include "esp_timer.h"
#include "lvgl.h"
#include "brookesia/gui_lvgl/image_decoding.hpp"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "freertos/idf_additions.h"

namespace espocket {
namespace {
constexpr const char *TAG = "ESPocket.RenderProbe";
constexpr uint32_t CACHE_BYTES = CONFIG_ESPOCKET_RUNTIME_IMAGE_CACHE_BYTES;
constexpr uint32_t DECODE_HEADROOM_BYTES = 64 * 1024;
namespace decoding = esp_brookesia::gui::lvgl;
#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE
lv_display_t *display=nullptr;
lv_timer_t *sample_timer=nullptr;
char app[96]{};
uint64_t window_start=0, render_start=0;
uint64_t draws=0, draw_us=0, draw_max_us=0;
bool rendered=false;
struct SampleLine { char text[640]{}; };
QueueHandle_t sample_queue=nullptr;
SemaphoreHandle_t logger_stopped=nullptr;
void log_samples(void *)
{
    SampleLine line;
    while (xQueueReceive(sample_queue,&line,portMAX_DELAY)==pdTRUE && line.text[0])
        ESP_LOGI(TAG,"%s",line.text);
    xSemaphoreGive(logger_stopped);
    vTaskDeleteWithCaps(nullptr);
}
#endif

#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE
void report()
{
    if (!app[0]) return;
    const auto now=static_cast<uint64_t>(esp_timer_get_time());
    const auto duration=now-window_start;
    if (!duration) return;
    uint32_t fps=0;
    const auto fps_status=esp_lv_adapter_get_fps(display,&fps);
    const auto decode = decoding::take_image_decode_statistics();
    SampleLine line;
    std::snprintf(line.text,sizeof(line.text),"app=%s window_us=%llu cache_limit=%lu png_open=%llu png_ok=%llu png_total_us=%llu png_max_us=%llu draw_frames=%llu draw_total_us=%llu draw_max_us=%llu completed_fps=%ld psram_free=%lu psram_largest=%lu pressure_evictions=%llu",
        app,static_cast<unsigned long long>(duration),static_cast<unsigned long>(CACHE_BYTES),
        static_cast<unsigned long long>(decode.attempts),static_cast<unsigned long long>(decode.successes),
        static_cast<unsigned long long>(decode.total_us),static_cast<unsigned long long>(decode.max_us),
        static_cast<unsigned long long>(draws),static_cast<unsigned long long>(draw_us),static_cast<unsigned long long>(draw_max_us),
        fps_status==ESP_OK?static_cast<long>(fps):-1L,
        static_cast<unsigned long>(heap_caps_get_free_size(MALLOC_CAP_SPIRAM)),static_cast<unsigned long>(heap_caps_get_largest_free_block(MALLOC_CAP_SPIRAM)),
        static_cast<unsigned long long>(decode.pressure_evictions));
    // Never wait for serial IO while holding the GUI lock. Only the latest
    // window is retained if the diagnostic consumer cannot keep up.
    (void)xQueueOverwrite(sample_queue,&line);
    window_start=now;draws=draw_us=draw_max_us=0;
}
void refresh_event(lv_event_t *event)
{
    if (!app[0]) return;
    const auto code=lv_event_get_code(event);
    if (code==LV_EVENT_RENDER_START) {render_start=esp_timer_get_time();rendered=true;}
    else if (code==LV_EVENT_RENDER_READY && rendered) {
        const auto elapsed=static_cast<uint64_t>(esp_timer_get_time())-render_start;
        ++draws;draw_us+=elapsed;draw_max_us=std::max(draw_max_us,elapsed);rendered=false;
    }
}
#endif
}
std::expected<void,std::string> initialize_runtime_render_probe()
{
    if (esp_lv_adapter_lock(2000)!=ESP_OK) return std::unexpected("render_probe_gui_busy");
    struct Unlock {~Unlock(){esp_lv_adapter_unlock();}} unlock;
    if (auto result = decoding::configure_image_decoding({CACHE_BYTES, DECODE_HEADROOM_BYTES}); !result) return result;
#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE
    display=lv_display_get_default();
    if (!display) return std::unexpected("render_probe_display_missing");
    if (esp_lv_adapter_fps_stats_enable(display,true)!=ESP_OK) return std::unexpected("render_probe_fps_unavailable");
    sample_queue=xQueueCreate(1,sizeof(SampleLine));
    logger_stopped=xSemaphoreCreateBinary();
    if (!sample_queue || !logger_stopped ||
        xTaskCreateWithCaps(log_samples,"RenderProbe",6144,nullptr,2,nullptr,MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT)!=pdPASS)
        return std::unexpected("render_probe_logger_allocation_failed");
    lv_display_add_event_cb(display,refresh_event,LV_EVENT_RENDER_START,nullptr);
    lv_display_add_event_cb(display,refresh_event,LV_EVENT_RENDER_READY,nullptr);
    sample_timer=lv_timer_create([](lv_timer_t*){report();},2000,nullptr);
    if (!sample_timer) return std::unexpected("render_probe_timer_allocation_failed");
    ESP_LOGI(TAG,"Initialized; bounded cache=%lu; decode counts are cache misses; FPS from completed last flush",static_cast<unsigned long>(CACHE_BYTES));
#endif
    return {};
}
void begin_runtime_render_probe(std::string_view manifest)
{
#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE
    if (esp_lv_adapter_lock(2000)!=ESP_OK) return;
    report();
    const auto size=std::min(manifest.size(),sizeof(app)-1);std::memcpy(app,manifest.data(),size);app[size]=0;
    window_start=esp_timer_get_time();decoding::set_image_decode_statistics_enabled(true);draws=draw_us=draw_max_us=0;rendered=false;
    (void)esp_lv_adapter_fps_stats_reset(display);
    esp_lv_adapter_unlock();
#else
    (void)manifest;
#endif
}
void end_runtime_render_probe()
{
#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE
    if (esp_lv_adapter_lock(2000)!=ESP_OK) return;
    report();app[0]=0;decoding::set_image_decode_statistics_enabled(false);rendered=false;esp_lv_adapter_unlock();
#endif
}
void shutdown_runtime_render_probe()
{
    if (esp_lv_adapter_lock(2000)!=ESP_OK) return;
#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE
    report();app[0]=0;
    if (sample_timer) {lv_timer_delete(sample_timer);sample_timer=nullptr;}
    if (display) {lv_display_remove_event_cb_with_user_data(display,refresh_event,nullptr);(void)esp_lv_adapter_fps_stats_enable(display,false);}
#endif
    decoding::release_image_decoding();
#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE
    display=nullptr;
#endif
    esp_lv_adapter_unlock();
#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE
    if (sample_queue && logger_stopped) {
        const SampleLine stop;
        (void)xQueueOverwrite(sample_queue,&stop);
        (void)xSemaphoreTake(logger_stopped,portMAX_DELAY);
        vQueueDelete(sample_queue);sample_queue=nullptr;
        vSemaphoreDelete(logger_stopped);logger_stopped=nullptr;
    }
#endif
}
}
