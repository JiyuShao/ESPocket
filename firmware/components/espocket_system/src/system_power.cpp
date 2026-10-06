#include "system_internal.hpp"

#include <algorithm>

namespace espocket {

void System::tick_runtime_package_policy(bool developer_enabled, uint64_t now_ms)
{
    constexpr uint32_t MAX_RETRY_MS = 30'000;
    if (developer_enabled) {
        package_developer_was_enabled_ = true;
        package_policy_retry_at_ms_ = 0;
        package_policy_retry_delay_ms_ = 1000;
        return;
    }
    if (!package_developer_was_enabled_ ||
            (package_policy_retry_at_ms_ != 0 && now_ms < package_policy_retry_at_ms_)) {
        return;
    }
    auto enforced = enforce_runtime_package_policy();
    if (enforced) {
        package_developer_was_enabled_ = false;
        package_policy_retry_at_ms_ = 0;
        package_policy_retry_delay_ms_ = 1000;
        return;
    }
    ESP_LOGE(TAG, "Developer package stop failed; retry in %" PRIu32 " ms: %s",
             package_policy_retry_delay_ms_, enforced.error().c_str());
    package_policy_retry_at_ms_ = now_ms + package_policy_retry_delay_ms_;
    package_policy_retry_delay_ms_ =
        std::min(package_policy_retry_delay_ms_ * 2, MAX_RETRY_MS);
}

void System::poll_system_input()
{
    // Keep product commands on the existing serialized App callback task.
    // Only System consumes hardware events; Shell supplies a generic tick.
    if (stopping_.load(std::memory_order_acquire)) {
        return;
    }
    tick_runtime_package_policy(
        developer_mode_ && developer_mode_->enabled(),
        static_cast<uint64_t>(esp_timer_get_time() / 1000)
    );
    const bool hardware_press = power_key_monitor_ && power_key_monitor_->take_short_press();
    if (hardware_press) {
        cancel_test_touch_.store(true, std::memory_order_release);
        if (test_power_input_ && test_power_input_->busy() && shell_) { shell_->cancel_gesture_input(); }
    }
    bool synthetic_press = false;
    if (test_power_input_) {
        if (!developer_mode_ || !developer_mode_->enabled()) {
            test_power_input_->cancel_pending();
        } else if (test_power_input_->expire(static_cast<uint64_t>(esp_timer_get_time() / 1000))) {
            ESP_LOGW(TAG, "Synthetic PWR expired before Owner execution");
        } else {
            (void)test_power_input_->execute_pending_context([this, &synthetic_press](uint64_t token) {
                if (foreground_token_->load(std::memory_order_acquire) == token) {
                    synthetic_press = true;
                    handle_power_short_press();
                } else {
                    ESP_LOGW(TAG, "Synthetic PWR cancelled after navigation task changed");
                }
            });
        }
    }
    if (hardware_press && !synthetic_press) {
        handle_power_short_press();
    }
    drain_runtime_navigation();
    drain_card_actions();
    if (test_snapshots_) { test_snapshots_->drain(); }
    tick_package_acceptance(static_cast<uint64_t>(esp_timer_get_time() / 1000));
}

void System::handle_power_short_press()
{
    if (stopping_.load(std::memory_order_acquire) || !shell_) {
        return;
    }

    shell_->discard_overlay_choices();

    if (!display_on_.load(std::memory_order_acquire)) {
        auto result = set_display_on(true);
        if (!result) {
            ESP_LOGW(TAG, "PWR wake failed: %s", result.error().c_str());
            return;
        }
        if (resume_app_id_ != esp_brookesia::system::core::INVALID_APP_ID) {
            auto active = get_active_app();
            auto app = get_app(resume_app_id_);
            if (!active.has_value() || active->app_id != resume_app_id_ ||
                    !app.has_value() || app->state != esp_brookesia::system::core::AppState::Running) {
                show_watch_face();
            }
        }
        resume_app_id_ = esp_brookesia::system::core::INVALID_APP_ID;
        ESP_LOGI(TAG, "M6 display state: Wake");
        return;
    }

    auto active = get_active_app();
    if (active.has_value() && active->app_id != shell_id_ && active->manifest.visible) {
        lifecycle_restore_surface_ = ShellSurface::WatchFace;
        lifecycle_restore_pending_ = true;
        auto result = stop_app(active->app_id);
        if (!result) {
            ESP_LOGW(TAG, "PWR Home failed to stop app: %s", result.error().c_str());
        }
        return;
    }

    if (!shell_->is_watch_face()) {
        show_watch_face();
        return;
    }

#if CONFIG_ESPOCKET_M6_RESOURCE_TRACE
    static uint32_t resource_sample = 0;
    ++resource_sample;
    ESP_LOGI(
        TAG,
        "M6_RESOURCE sample=%" PRIu32 " internal_free=%zu psram_free=%zu internal_largest=%zu psram_largest=%zu",
        resource_sample,
        heap_caps_get_free_size(MALLOC_CAP_INTERNAL),
        heap_caps_get_free_size(MALLOC_CAP_SPIRAM),
        heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL),
        heap_caps_get_largest_free_block(MALLOC_CAP_SPIRAM)
    );
#ifdef CONFIG_BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE
    constexpr int async_stack_budget = CONFIG_BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE;
#else
    constexpr int async_stack_budget = 8 * 1024;
#endif
    if (const auto worker = xTaskGetHandle("RuntimeJsAsync")) {
        ESP_LOGI(TAG, "M8_RUNTIME_STACK sample=%" PRIu32 " budget=%d minimum_free=%u",
                 resource_sample, async_stack_budget,
                 static_cast<unsigned>(uxTaskGetStackHighWaterMark(worker)));
    }
#endif

    auto result = set_display_on(false);
    if (!result) {
        ESP_LOGW(TAG, "PWR screen-off failed: %s", result.error().c_str());
    }
}

} // namespace espocket
