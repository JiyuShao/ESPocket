#include "espocket/settings_navigation_adapter.hpp"

#include <array>
#include <utility>

#include "esp_log.h"

namespace espocket {
namespace {
constexpr char TAG[] = "ESPocket.Settings";
constexpr std::string_view CONTENT_FLOW = "settings_content";
constexpr std::string_view BACK_ACTION = "settings.header.back";
constexpr std::array<std::pair<std::string_view, std::string_view>, 10> PAGE_IDS{{
    {"settings_home", "settings.root"},
    {"my_device", "settings.device"},
    {"wifi", "settings.wifi"},
    {"wifi_connect", "settings.wifi_connect"},
    {"sound", "settings.sound"},
    {"display", "settings.display"},
    {"more", "settings.more"},
    {"language", "settings.language"},
    {"time_zone", "settings.time_zone"},
    {"debug", "settings.debug"},
}};
} // namespace

using AppContext = esp_brookesia::system::core::AppContext;

SettingsNavigationAdapter::SettingsNavigationAdapter(
    std::shared_ptr<esp_brookesia::system::core::IApp> app
) : app_(std::move(app)), app_id_(app_->get_manifest().id) {}

esp_brookesia::system::core::AppManifest SettingsNavigationAdapter::get_manifest() const
{
    return app_->get_manifest();
}

esp_brookesia::system::core::AppGuiDescriptor SettingsNavigationAdapter::get_gui_descriptor() const
{
    return app_->get_gui_descriptor();
}

std::expected<void, std::string> SettingsNavigationAdapter::on_install(AppContext &context)
{
    std::lock_guard lock(mutex_);
    return app_->on_install(context);
}

void SettingsNavigationAdapter::on_uninstall(AppContext &context)
{
    std::lock_guard lock(mutex_);
    context_ = nullptr;
    edge_enabled_.store(false, std::memory_order_release);
    app_->on_uninstall(context);
}

std::expected<void, std::string> SettingsNavigationAdapter::on_start(AppContext &context)
{
    std::lock_guard lock(mutex_);
    context_ = nullptr;
    edge_enabled_.store(false, std::memory_order_release);
    auto result = app_->on_start(context);
    if (result) {
        context_ = &context;
        refresh_availability();
    }
    return result;
}

std::expected<void, std::string> SettingsNavigationAdapter::on_pause(AppContext &context)
{
    std::lock_guard lock(mutex_);
    auto result = app_->on_pause(context);
    if (result) {
        context_ = nullptr;
    }
    edge_enabled_.store(false, std::memory_order_release);
    return result;
}

std::expected<void, std::string> SettingsNavigationAdapter::on_resume(AppContext &context)
{
    std::lock_guard lock(mutex_);
    auto result = app_->on_resume(context);
    if (result) {
        context_ = &context;
    }
    refresh_availability();
    return result;
}

std::expected<void, std::string> SettingsNavigationAdapter::on_stop(AppContext &context)
{
    std::lock_guard lock(mutex_);
    context_ = nullptr;
    edge_enabled_.store(false, std::memory_order_release);
    return app_->on_stop(context);
}

std::expected<void, std::string> SettingsNavigationAdapter::on_action(
    AppContext &context, std::string_view action
)
{
    std::lock_guard lock(mutex_);
    if (action == BACK_ACTION) {
        return request_back();
    }
    auto result = app_->on_action(context, action);
    refresh_availability();
    return result;
}

std::expected<void, std::string> SettingsNavigationAdapter::on_timer(
    AppContext &context, esp_brookesia::system::core::TimerId timer_id, std::string_view name
)
{
    std::lock_guard lock(mutex_);
    auto result = app_->on_timer(context, timer_id, name);
    refresh_availability();
    return result;
}

std::expected<PageSnapshot, std::string> SettingsNavigationAdapter::snapshot() const
{
    std::lock_guard lock(mutex_);
    if (!context_) {
        return std::unexpected("not_started");
    }
    auto screen = context_->gui().get_screen_flow_state(CONTENT_FLOW);
    if (!screen) {
        return std::unexpected("settings_flow_unavailable");
    }
    for (const auto &[upstream_id, page_id] : PAGE_IDS) {
        if (*screen == upstream_id) {
            return PageSnapshot{
                .app_id = app_id_,
                .page_id = std::string(page_id),
                .can_back = upstream_id != "settings_home",
                .back_pending = false,
            };
        }
    }
    return std::unexpected("unknown_settings_page: " + *screen);
}

std::expected<void, std::string> SettingsNavigationAdapter::request_back()
{
    std::lock_guard lock(mutex_);
    auto page = snapshot();
    if (!page) {
        refresh_availability();
        return std::unexpected(page.error());
    }
    if (!page->can_back) {
        return std::unexpected("at_root");
    }
    auto result = app_->on_action(*context_, BACK_ACTION);
    refresh_availability();
    return result;
}

bool SettingsNavigationAdapter::edge_back_enabled() const
{
    return edge_enabled_.load(std::memory_order_acquire);
}

void SettingsNavigationAdapter::refresh()
{
    std::lock_guard lock(mutex_);
    refresh_availability();
}

void SettingsNavigationAdapter::refresh_availability()
{
    auto page = snapshot();
    edge_enabled_.store(page && page->can_back, std::memory_order_release);
    const auto error = page ? std::string{} : page.error();
    if (!error.empty() && error != last_error_) {
        ESP_LOGW(TAG, "Settings Page adapter unavailable: %s", error.c_str());
    }
    last_error_ = error;
}

} // namespace espocket
