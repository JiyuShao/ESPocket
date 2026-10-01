#pragma once

#include <atomic>
#include <cstdint>
#include <expected>
#include <memory>
#include <string>
#include <string_view>
#include <unordered_map>

#include "brookesia/service_manager/service/manager.hpp"
#include "brookesia/system_core.hpp"
#include "espocket/page_navigator.hpp"

namespace espocket {

class CircularShell;
class PowerKeyMonitor;
class PageNavigator;
class DeveloperMode;
class InteractionTestAdapter;
class SettingsNavigationAdapter;
enum class ShellSurface : uint8_t;

class System final : public esp_brookesia::system::core::System {
public:
    System();
    ~System() override;
    std::expected<void, std::string> init();
    std::expected<PageSnapshot, std::string> foreground_page_snapshot() const;

protected:
    esp_brookesia::system::core::SystemInfo on_get_system_info() const override;
    std::expected<void, std::string> on_init() override;
    std::expected<void, std::string> on_start() override;
    void on_stop() override;
    void on_deinit() override;
    std::expected<void, std::string> on_app_started(
        const esp_brookesia::system::core::AppInfo &app
    ) override;
    void on_app_start_failed(
        const esp_brookesia::system::core::AppInfo &app,
        std::string_view reason
    ) override;
    void on_app_stopped(const esp_brookesia::system::core::AppInfo &app) override;
    void on_app_stop_failed(
        const esp_brookesia::system::core::AppInfo &app,
        std::string_view reason
    ) override;
    std::expected<void, std::string> on_show_app_keyboard(
        esp_brookesia::system::core::AppId app_id,
        esp_brookesia::system::core::KeyboardRequestId request_id,
        const esp_brookesia::system::core::KeyboardRequestOptions &options
    ) override;
    void on_hide_app_keyboard(
        esp_brookesia::system::core::AppId app_id,
        esp_brookesia::system::core::KeyboardRequestId request_id
    ) override;

private:
    std::expected<void, std::string> start_display();
    void poll_system_input();
    void handle_power_short_press();
    void handle_screen_timeout();
    void handle_back();
    void handle_back_timeout();
    std::expected<void, std::string> launch_app(std::string_view manifest_id, ShellSurface source);
    std::expected<void, std::string> set_display_on(bool on);
    void show_watch_face();
    void restore_surface(ShellSurface surface);
    void clear_foreground(const esp_brookesia::system::core::AppInfo &app);
    void restore_home_after_lifecycle(const esp_brookesia::system::core::AppInfo &app);
    std::shared_ptr<PageNavigator> navigator_for(esp_brookesia::system::core::AppId app_id) const;
    void register_navigator(
        esp_brookesia::system::core::AppId app_id,
        std::shared_ptr<PageNavigator> navigator
    );

    esp_brookesia::service::ServiceBinding display_binding_;
    std::shared_ptr<CircularShell> shell_;
    std::shared_ptr<SettingsNavigationAdapter> settings_adapter_;
    esp_brookesia::system::core::AppId settings_id_ = esp_brookesia::system::core::INVALID_APP_ID;
    std::unordered_map<esp_brookesia::system::core::AppId, std::shared_ptr<PageNavigator>> page_navigators_;
    std::shared_ptr<DeveloperMode> developer_mode_;
    std::unique_ptr<InteractionTestAdapter> test_adapter_;
    std::unique_ptr<PowerKeyMonitor> power_key_monitor_;
    std::shared_ptr<std::atomic<uint64_t>> foreground_token_ =
        std::make_shared<std::atomic<uint64_t>>(0);
    esp_brookesia::system::core::AppId shell_id_ = esp_brookesia::system::core::INVALID_APP_ID;
    std::atomic_bool default_back_visible_ = false;
    std::atomic_bool edge_back_enabled_ = false;
    std::atomic<esp_brookesia::system::core::AppId> foreground_app_id_{
        esp_brookesia::system::core::INVALID_APP_ID
    };
    uint64_t foreground_generation_ = 0;
    uint32_t display_width_ = 0;
    uint32_t display_height_ = 0;
    uint32_t display_output_id_ = 0;
    bool display_started_ = false;
    std::atomic_bool display_on_ = true;
    esp_brookesia::system::core::AppId resume_app_id_ =
        esp_brookesia::system::core::INVALID_APP_ID;
    ShellSurface launch_source_;
    ShellSurface lifecycle_restore_surface_;
    bool lifecycle_restore_pending_ = false;
    std::atomic_bool stopping_ = false;
    std::atomic_bool runtime_stop_failed_ = false;
};

} // namespace espocket
