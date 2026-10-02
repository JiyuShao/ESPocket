#include "espocket/system.hpp"
#include "sdkconfig.h"
#include "esp_log.h"
#include <cinttypes>

namespace espocket {
namespace { constexpr char TAG[] = "ESPocket.System"; }
namespace {
#if CONFIG_ESPOCKET_M6_RECLAIM_ON_TIMEOUT_TEST
constexpr bool RECLAIM_BOTH = true;
#else
constexpr bool RECLAIM_BOTH = false;
#endif
#if CONFIG_ESPOCKET_M8_RECLAIM_NATIVE_TEST
constexpr bool RECLAIM_NATIVE = true;
#else
constexpr bool RECLAIM_NATIVE = false;
#endif
#if CONFIG_ESPOCKET_M8_RECLAIM_RUNTIME_TEST
constexpr bool RECLAIM_RUNTIME = true;
#else
constexpr bool RECLAIM_RUNTIME = false;
#endif
}

void System::handle_screen_timeout()
{
    if (stopping_.load(std::memory_order_acquire) ||
            !display_on_.load(std::memory_order_acquire)) {
        return;
    }
    auto result = set_display_on(false);
    if (!result) {
        ESP_LOGW(TAG, "Automatic screen-off failed: %s", result.error().c_str());
        return;
    }

#if CONFIG_ESPOCKET_M6_RECLAIM_ON_TIMEOUT_TEST || CONFIG_ESPOCKET_M8_RECLAIM_NATIVE_TEST || CONFIG_ESPOCKET_M8_RECLAIM_RUNTIME_TEST
    if (resume_app_id_ != esp_brookesia::system::core::INVALID_APP_ID) {
        const auto target = resume_app_id_;
        const auto app = get_app(target);
        using esp_brookesia::system::core::AppKind;
        const bool selected = app && app->manifest.visible &&
            ((app->manifest.kind == AppKind::Native &&
              (RECLAIM_BOTH || RECLAIM_NATIVE)) ||
             (app->manifest.kind == AppKind::Runtime &&
              (RECLAIM_BOTH || RECLAIM_RUNTIME)));
        if (!selected) return;
        auto stop_result = stop_app(target);
        if (!stop_result) {
            ESP_LOGE(TAG, "M6_RECLAIM_TEST failed to stop App: %s", stop_result.error().c_str());
        } else {
            if constexpr (RECLAIM_BOTH) {
                ESP_LOGI(TAG, "M6_RECLAIM_TEST stopped resume target app_id=%" PRIu32, target);
            }
            ESP_LOGI(TAG, "APP_RECLAIM_TEST stopped model=%s manifest=%s app_id=%" PRIu32,
                     app->manifest.kind == AppKind::Native ? "native" : "runtime",
                     app->manifest.id.c_str(), target);
        }
    }
#endif
}

} // namespace espocket
