#include "system_internal.hpp"

namespace espocket {

std::expected<TestSnapshot, std::string> System::read_test_snapshot() const
{
    if (stopping_.load(std::memory_order_acquire) || !shell_) {
        return std::unexpected("system_unavailable");
    }
    const auto token = foreground_token_->load(std::memory_order_acquire);
    const auto surface = shell_->current_surface();
    const auto display = display_on_.load(std::memory_order_acquire);
    TestSnapshot snapshot;
    snapshot.display = display;
    snapshot.input_busy = test_power_input_ && test_power_input_->busy();
    switch (surface) {
    case ShellSurface::WatchFace: snapshot.surface = "watch_face"; break;
    case ShellSurface::Launcher: snapshot.surface = "launcher"; break;
    case ShellSurface::QuickSettings: snapshot.surface = "quick_settings"; break;
    case ShellSurface::BatteryCard: snapshot.surface = "shell.battery"; break;
    case ShellSurface::BrightnessCard: snapshot.surface = "shell.brightness"; break;
    }
    if (token != 0) {
        auto page = foreground_page_snapshot();
        if (!page) {
            return std::unexpected(page.error());
        }
        snapshot.foreground_app_id = page->app_id;
        snapshot.page_id = page->page_id;
        snapshot.can_back = page->can_back;
        snapshot.back_pending = page->back_pending;
    }
    if (foreground_token_->load(std::memory_order_acquire) != token ||
            shell_->current_surface() != surface ||
            display_on_.load(std::memory_order_acquire) != display ||
            stopping_.load(std::memory_order_acquire)) {
        return std::unexpected("state_changed");
    }
    return snapshot;
}

std::expected<void, std::string> System::launch_app(
    std::string_view manifest_id,
    ShellSurface source
)
{
    auto apps = list_apps();
    auto app = std::find_if(apps.begin(), apps.end(), [manifest_id](const auto &candidate) {
        return candidate.manifest.id == manifest_id;
    });
    if (app == apps.end()) {
        return std::unexpected("App is not installed: " + std::string(manifest_id));
    }
    launch_source_ = source;
    lifecycle_restore_surface_ = source;
    lifecycle_restore_pending_ = true;
    auto result = start_app(app->app_id);
    if (!result) {
        restore_surface(source);
        lifecycle_restore_pending_ = false;
        return result;
    }
    return {};
}

void System::handle_back()
{
    if (stopping_.load(std::memory_order_acquire) || !shell_) {
        return;
    }
    auto active = get_active_app();
    if (!active.has_value() || active->app_id == shell_id_ || !active->manifest.visible) {
        if (shell_->current_surface() != ShellSurface::WatchFace) {
            restore_surface(ShellSurface::WatchFace);
        }
        return;
    }

    if (active->app_id == settings_id_ && settings_adapter_) {
        auto result = settings_adapter_->request_back();
        if (!result && result.error() != "at_root") {
            ESP_LOGW(TAG, "Settings Back failed: %s", result.error().c_str());
        }
        return;
    }
    if (auto navigator = navigator_for(active->app_id)) {
        if (!runtime_page_matches(active->app_id)) {
            default_back_visible_.store(false);
            edge_back_enabled_.store(false);
            ESP_LOGW(TAG, "Runtime Page and Screen Flow disagree; Back disabled");
            return;
        }
        if (!navigator->edge_back_enabled()) {
            return;
        }
        auto result = navigator->request_back(
            static_cast<uint64_t>(esp_timer_get_time() / 1000)
        );
        if (!result) {
            ESP_LOGW(TAG, "App Page Back failed: %d", static_cast<int>(result.error()));
        }
    }
}

void System::handle_back_timeout()
{
    if (foreground_app_id_.load(std::memory_order_acquire) == settings_id_ && settings_adapter_) {
        settings_adapter_->refresh();
        return;
    }
    auto navigator = navigator_for(foreground_app_id_.load(std::memory_order_acquire));
    if (!navigator) {
        return;
    }
    const auto expired = navigator->expire_back(
        static_cast<uint64_t>(esp_timer_get_time() / 1000)
    );
    if (expired) {
        ESP_LOGW(TAG, "App Back confirmation timed out: %d", static_cast<int>(*expired));
    }
}

void System::show_watch_face()
{
    if (!shell_) {
        return;
    }
    auto result = shell_->show_watch_face();
    if (!result) {
        ESP_LOGW(TAG, "Failed to show Watch Face: %s", result.error().c_str());
    } else {
        ESP_LOGI(TAG, "M6 Home: Watch Face");
    }
}

void System::restore_surface(ShellSurface surface)
{
    if (!shell_) {
        return;
    }
    auto result = shell_->show_surface(surface);
    if (!result) {
        ESP_LOGW(TAG, "Failed to restore Shell surface: %s", result.error().c_str());
        if (surface != ShellSurface::WatchFace) {
            show_watch_face();
        }
    }
}

std::shared_ptr<PageNavigator> System::navigator_for(
    esp_brookesia::system::core::AppId app_id
) const
{
    std::lock_guard lock(page_navigators_mutex_);
    const auto it = page_navigators_.find(app_id);
    return it == page_navigators_.end() ? nullptr : it->second;
}

std::expected<InstalledPageApp, std::string> System::install_navigated_app(
    std::shared_ptr<esp_brookesia::system::core::IApp> app,
    PageDeclaration declaration,
    PageNavigator::Presenter presenter
)
{
    auto installed = install_native_page_app(*this, std::move(app), std::move(declaration),
                                             std::move(presenter));
    if (!installed) {
        return installed;
    }
    register_navigator(installed->app_id, installed->navigator);
    return installed;
}

std::expected<PageSnapshot, std::string> System::foreground_page_snapshot() const
{
    const auto token = foreground_token_->load(std::memory_order_acquire);
    const auto app_id = foreground_app_id_.load(std::memory_order_acquire);
    if (token == 0 || app_id == esp_brookesia::system::core::INVALID_APP_ID) {
        return std::unexpected("no_foreground_app");
    }
    std::expected<PageSnapshot, std::string> result = std::unexpected("page_adapter_unavailable");
    if (app_id == settings_id_ && settings_adapter_) {
        result = settings_adapter_->snapshot();
    } else if (auto navigator = navigator_for(app_id)) {
        if (!runtime_page_matches(app_id)) return std::unexpected("invalid_state");
        auto page = navigator->snapshot();
        result = page.page_id.empty() ? std::expected<PageSnapshot, std::string>(
            std::unexpected("not_started")) : std::expected<PageSnapshot, std::string>(std::move(page));
    }
    if (foreground_token_->load(std::memory_order_acquire) != token ||
            foreground_app_id_.load(std::memory_order_acquire) != app_id) {
        return std::unexpected("foreground_changed");
    }
    return result;
}

void System::register_navigator(
    esp_brookesia::system::core::AppId app_id,
    std::shared_ptr<PageNavigator> navigator
)
{
    navigator->set_availability_handler([this, app_id](bool default_visible, bool edge_enabled) {
        if (foreground_app_id_.load(std::memory_order_acquire) != app_id) {
            return;
        }
        default_back_visible_.store(default_visible, std::memory_order_release);
        edge_back_enabled_.store(edge_enabled, std::memory_order_release);
    });
    std::lock_guard lock(page_navigators_mutex_);
    page_navigators_.emplace(app_id, std::move(navigator));
}

} // namespace espocket
