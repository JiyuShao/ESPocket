#include "system_internal.hpp"

namespace espocket {

std::expected<void, std::string> System::on_app_uninstalled(
    const esp_brookesia::system::core::AppInfo &app
)
{
    if (cards_ && cards_->uninstall_app(app.manifest.id)) {
        if (auto saved = card_store_->save_current(); !saved) {
            ESP_LOGE(TAG, "Card uninstall persistence failed: %s", saved.error().c_str());
        }
    }
    card_factories_.erase(app.app_id);
    std::shared_ptr<PageNavigator> removed;
    {
        std::lock_guard lock(page_navigators_mutex_);
        const auto it = page_navigators_.find(app.app_id);
        if (it != page_navigators_.end()) {
            removed = std::move(it->second);
            page_navigators_.erase(it);
        }
        runtime_pages_.erase(app.app_id);
    }
    if (removed) {
        removed->stop();
        removed->set_availability_handler({});
    }
    clear_foreground(app);
    return {};
}

std::expected<void, std::string> System::on_app_started(
    const esp_brookesia::system::core::AppInfo &app
)
{
    if (stopping_.load(std::memory_order_acquire)) {
        return std::unexpected("ESPocket System is stopping");
    }
    if (app.app_id == shell_id_ || !app.manifest.visible) {
        return {};
    }

    if (auto navigator = navigator_for(app.app_id)) {
        const auto runtime = runtime_adapter_for(app.app_id);
        auto result = runtime ? runtime->start() : navigator->start();
        if (!result) {
            return std::unexpected("Failed to start App Page Navigator");
        }
        if (runtime && !runtime_page_matches(app.app_id)) {
            runtime->stop();
            return std::unexpected("Runtime initial Screen Flow does not match Root Page");
        }
        if (runtime) {
            // The locked JS backend drains Promise completions on a subsequent callback.
            // Provide that callback even when the App has no timer or input activity.
            const auto pump = timer_start_periodic(app.app_id, "espocket.navigation.completion", 50);
            if (!pump) return std::unexpected("Failed to start Runtime completion pump: " + pump.error());
        }
    }

    pause_card();
    foreground_app_id_.store(app.app_id, std::memory_order_release);
    do {
        ++foreground_generation_;
    } while (foreground_generation_ == 0);
    foreground_token_->store(foreground_generation_, std::memory_order_release);
    if (pending_card_ && pending_card_->app_id == app.manifest.id) {
        const auto target = cards_->target_page(*pending_card_);
        auto navigator = navigator_for(app.app_id);
        if (!target || !navigator || (*target != navigator->snapshot().page_id && !navigator->push(*target))) {
            ESP_LOGW(TAG, "Card target_unavailable: app=%s card=%s; no target Page committed", pending_card_->app_id.c_str(), pending_card_->card_id.c_str());
        }
    }
    const auto navigator = navigator_for(app.app_id);
    default_back_visible_.store(navigator && navigator->show_default_back(),
                               std::memory_order_release);
    edge_back_enabled_.store(navigator && navigator->edge_back_enabled(),
                            std::memory_order_release);
    lifecycle_restore_pending_ = false;
    return {};
}

void System::on_app_start_failed(
    const esp_brookesia::system::core::AppInfo &app,
    std::string_view reason
)
{
    if (auto runtime = runtime_adapter_for(app.app_id)) {
        runtime->stop();
    } else if (auto navigator = navigator_for(app.app_id)) {
        navigator->stop();
    }
    ESP_LOGW(
        TAG,
        "App start failed: manifest=%s reason=%.*s",
        app.manifest.id.c_str(),
        static_cast<int>(reason.size()),
        reason.data()
    );
    restore_home_after_lifecycle(app);
}

void System::on_app_stopped(const esp_brookesia::system::core::AppInfo &app)
{
    if (auto runtime = runtime_adapter_for(app.app_id)) {
        runtime->stop();
    } else if (auto navigator = navigator_for(app.app_id)) {
        navigator->stop();
    }
    restore_home_after_lifecycle(app);
}

void System::on_app_stop_failed(
    const esp_brookesia::system::core::AppInfo &app,
    std::string_view reason
)
{
    if (auto runtime = runtime_adapter_for(app.app_id)) {
        runtime->stop();
    } else if (auto navigator = navigator_for(app.app_id)) {
        navigator->stop();
    }
    ESP_LOGW(
        TAG,
        "App stop failed: manifest=%s reason=%.*s",
        app.manifest.id.c_str(),
        static_cast<int>(reason.size()),
        reason.data()
    );
    if (app.manifest.kind == esp_brookesia::system::core::AppKind::Runtime) {
        runtime_stop_failed_.store(true, std::memory_order_release);
        ESP_LOGE(TAG, "Keyboard input disabled after Runtime stop failure");
    }
    restore_home_after_lifecycle(app);
}

std::expected<void, std::string> System::on_show_app_keyboard(
    esp_brookesia::system::core::AppId app_id,
    esp_brookesia::system::core::KeyboardRequestId request_id,
    const esp_brookesia::system::core::KeyboardRequestOptions &options
)
{
    if (runtime_stop_failed_.load(std::memory_order_acquire)) {
        return std::unexpected("Keyboard input is disabled until restart after Runtime stop failure");
    }
    auto app = get_app(app_id);
    if (!app.has_value()) {
        return std::unexpected("Keyboard owner app is not installed");
    }
    if (app->state != esp_brookesia::system::core::AppState::Running) {
        return std::unexpected("Keyboard input requires a running owner app");
    }
    if (!shell_) {
        return std::unexpected("Circular Shell is unavailable for keyboard input");
    }
    return shell_->show_keyboard(app_id, request_id, options);
}

void System::on_hide_app_keyboard(
    esp_brookesia::system::core::AppId app_id,
    esp_brookesia::system::core::KeyboardRequestId request_id
)
{
    if (shell_) {
        shell_->hide_keyboard(app_id, request_id);
    }
}

void System::clear_foreground(
    const esp_brookesia::system::core::AppInfo &app
)
{
    auto expected = app.app_id;
    if (!foreground_app_id_.compare_exchange_strong(
                expected,
                esp_brookesia::system::core::INVALID_APP_ID,
                std::memory_order_acq_rel
            )) {
        return;
    }
    foreground_token_->store(0, std::memory_order_release);
}

void System::restore_home_after_lifecycle(
    const esp_brookesia::system::core::AppInfo &app
)
{
    clear_foreground(app);
    if (stopping_.load(std::memory_order_acquire) || app.app_id == shell_id_ ||
            !app.manifest.visible || !shell_) {
        return;
    }

    auto active = get_active_app();
    if (active.has_value() && active->app_id != shell_id_ && active->manifest.visible) {
        return;
    }

    auto shell = get_app(shell_id_);
    if (!shell.has_value() || shell->state != esp_brookesia::system::core::AppState::Running) {
        return;
    }
    const auto surface = lifecycle_restore_pending_ ? lifecycle_restore_surface_ : ShellSurface::WatchFace;
    lifecycle_restore_pending_ = false;
    restore_surface(surface);
}

} // namespace espocket
