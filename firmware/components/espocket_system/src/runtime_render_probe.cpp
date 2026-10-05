#include "runtime_render_probe.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <cstdio>
#include "sdkconfig.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_lv_adapter.h"
#include "esp_timer.h"
#include "lvgl.h"
#include "src/draw/lv_image_decoder_private.h"
#include "src/misc/cache/instance/lv_image_cache.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "freertos/idf_additions.h"

namespace espocket {
namespace {
constexpr const char *TAG = "ESPocket.RenderProbe";
constexpr uint32_t CACHE_BYTES = CONFIG_ESPOCKET_RUNTIME_IMAGE_CACHE_BYTES;
constexpr uint64_t DECODE_HEADROOM_BYTES = 64 * 1024;
struct DecoderHook { lv_image_decoder_t *decoder=nullptr; lv_image_decoder_open_f_t open=nullptr; };
std::array<DecoderHook, 8> hooks;
#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE
lv_display_t *display=nullptr;
lv_timer_t *sample_timer=nullptr;
char app[96]{};
uint64_t window_start=0, render_start=0;
uint64_t png_attempts=0, png_success=0, png_us=0, png_max_us=0;
uint64_t pressure_evictions=0;
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

[[maybe_unused]] bool is_png(const lv_image_decoder_dsc_t *dsc)
{
    if (dsc->src_type == LV_IMAGE_SRC_FILE) {
        const auto *name=static_cast<const char *>(dsc->src);
        const auto size=std::strlen(name);
        return size >= 4 && std::strcmp(name+size-4, ".png") == 0;
    }
    if (dsc->src_type != LV_IMAGE_SRC_VARIABLE) return false;
    const auto *source=static_cast<const lv_image_dsc_t *>(dsc->src);
    constexpr uint8_t signature[]{137,80,78,71,13,10,26,10};
    return source && source->data && source->data_size >= sizeof(signature) &&
           std::memcmp(source->data, signature, sizeof(signature)) == 0;
}
lv_result_t measured_open(lv_image_decoder_t *decoder, lv_image_decoder_dsc_t *dsc)
{
    auto found=std::find_if(hooks.begin(), hooks.end(), [decoder](const auto &hook){return hook.decoder==decoder;});
    if (found==hooks.end() || !found->open) return LV_RESULT_INVALID;
    [[maybe_unused]] const bool png=is_png(dsc);
    // Oversized images stay renderable without occupying the bounded cache.
    // ARGB8888 bounds the locked decoders' normal output. The cache is
    // shared with Native images, so this fallback must cover their decoders too.
    const auto decoded_bytes=static_cast<uint64_t>(lv_draw_buf_width_to_stride(dsc->header.w,LV_COLOR_FORMAT_ARGB8888))*dsc->header.h;
    if (CACHE_BYTES && decoded_bytes > CACHE_BYTES)
        dsc->args.no_cache=true;
    // A byte budget alone cannot guarantee a contiguous decode allocation.
    // Release retained images before allocating a large PNG, leaving workspace
    // for libpng as well. This also applies to images bypassing the cache.
    if (png && CACHE_BYTES &&
        (heap_caps_get_largest_free_block(MALLOC_CAP_SPIRAM) < decoded_bytes ||
         heap_caps_get_free_size(MALLOC_CAP_SPIRAM) < decoded_bytes + DECODE_HEADROOM_BYTES)) {
        lv_image_cache_drop(nullptr);
#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE
        if (app[0]) ++pressure_evictions;
#endif
    }
#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE
    const auto start=esp_timer_get_time();
#endif
    const auto result=found->open(decoder,dsc);
#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE
    if (app[0] && png) {
        const auto elapsed=static_cast<uint64_t>(esp_timer_get_time()-start);
        ++png_attempts; png_success += result == LV_RESULT_OK;
        png_us += elapsed; png_max_us=std::max(png_max_us,elapsed);
    }
#endif
    return result;
}
#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE
void report()
{
    if (!app[0]) return;
    const auto now=static_cast<uint64_t>(esp_timer_get_time());
    const auto duration=now-window_start;
    if (!duration) return;
    uint32_t fps=0;
    const auto fps_status=esp_lv_adapter_get_fps(display,&fps);
    SampleLine line;
    std::snprintf(line.text,sizeof(line.text),"app=%s window_us=%llu cache_limit=%lu png_open=%llu png_ok=%llu png_total_us=%llu png_max_us=%llu draw_frames=%llu draw_total_us=%llu draw_max_us=%llu completed_fps=%ld psram_free=%lu psram_largest=%lu pressure_evictions=%llu",
        app,static_cast<unsigned long long>(duration),static_cast<unsigned long>(CACHE_BYTES),
        static_cast<unsigned long long>(png_attempts),static_cast<unsigned long long>(png_success),
        static_cast<unsigned long long>(png_us),static_cast<unsigned long long>(png_max_us),
        static_cast<unsigned long long>(draws),static_cast<unsigned long long>(draw_us),static_cast<unsigned long long>(draw_max_us),
        fps_status==ESP_OK?static_cast<long>(fps):-1L,
        static_cast<unsigned long>(heap_caps_get_free_size(MALLOC_CAP_SPIRAM)),static_cast<unsigned long>(heap_caps_get_largest_free_block(MALLOC_CAP_SPIRAM)),
        static_cast<unsigned long long>(pressure_evictions));
    // Never wait for serial IO while holding the GUI lock. Only the latest
    // window is retained if the diagnostic consumer cannot keep up.
    (void)xQueueOverwrite(sample_queue,&line);
    window_start=now;png_attempts=png_success=png_us=png_max_us=pressure_evictions=0;draws=draw_us=draw_max_us=0;
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
    lv_image_cache_resize(CACHE_BYTES,true);
    size_t used=0;
    for (auto *decoder=lv_image_decoder_get_next(nullptr);decoder;decoder=lv_image_decoder_get_next(decoder)) {
        if (!decoder->open_cb) continue;
        if (used==hooks.size()) return std::unexpected("render_probe_decoder_capacity");
        hooks[used++]={decoder,decoder->open_cb};lv_image_decoder_set_open_cb(decoder,measured_open);
    }
    if (!used) return std::unexpected("render_probe_png_decoder_missing");
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
    window_start=esp_timer_get_time();png_attempts=png_success=png_us=png_max_us=pressure_evictions=0;draws=draw_us=draw_max_us=0;rendered=false;
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
    report();app[0]=0;rendered=false;esp_lv_adapter_unlock();
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
    for (auto &hook:hooks) {if(hook.decoder)lv_image_decoder_set_open_cb(hook.decoder,hook.open);hook={};}
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
