#pragma once

#include <atomic>
#include <cstdint>
#include <expected>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

#include "brookesia/service_manager/service/manager.hpp"
#include "brookesia/system_core.hpp"
#include "espocket/page_navigator.hpp"
#include "espocket/native_page_installation.hpp"
#include "espocket/card_registry.hpp"
#include "espocket/card_model.hpp"
#include "espocket/brightness.hpp"

namespace espocket {

class CircularShell;
class PowerKeyMonitor;
class TestInputQueue;
class TouchInputSequence;
class OwnerSnapshotQueue;
struct TouchInputStep;
class PageNavigator;
class DeveloperMode;
class InteractionTestAdapter;
class SettingsNavigationAdapter;
class RuntimePageAdapter;
class NavigationRequestQueue;
class CardConfigurationStore;
class CardSession;
struct TestSnapshot;
enum class ShellSurface : uint8_t;

class System final : public esp_brookesia::system::core::System {
public:
    System();
    ~System() override;
    std::expected<void, std::string> init();
    std::expected<PageSnapshot, std::string> foreground_page_snapshot() const;
    std::expected<InstalledPageApp, std::string> install_navigated_app(
        std::shared_ptr<esp_brookesia::system::core::IApp> app,
        PageDeclaration declaration,
        PageNavigator::Presenter presenter,
        CardModelFactory cards = {}
    );
    // Invoke from the serialized App owner, as for installation and declaration update.
    std::expected<void, std::string> configure_cards(CardConfiguration configuration);
    CardConfiguration card_configuration() const;
    std::vector<CardKey> available_cards() const;
    std::expected<void, std::string> update_navigated_declaration(
        esp_brookesia::system::core::AppId id, PageDeclaration declaration);

protected:
    esp_brookesia::system::core::SystemInfo on_get_system_info() const override;
    std::expected<void, std::string> on_init() override;
    std::expected<void, std::string> on_start() override;
    void on_stop() override;
    void on_deinit() override;
    std::expected<void, std::string> on_app_installed(
        const esp_brookesia::system::core::AppInfo &app) override;
    std::expected<void, std::string> on_app_uninstalled(
        const esp_brookesia::system::core::AppInfo &app
    ) override;
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
    void init_cards();
    std::expected<void, std::string> init_card_samples();
    std::expected<void, std::string> step_card(bool left, bool inward);
    void card_surface_changed(ShellSurface surface);
    void drain_card_actions();
    void pause_card();
    std::expected<void, std::string> resume_card();
    void init_runtime_navigation();
    void stop_runtime_navigation();
    void drain_runtime_navigation();
    std::shared_ptr<RuntimePageAdapter> runtime_adapter_for(esp_brookesia::system::core::AppId id) const;
    bool runtime_page_matches(esp_brookesia::system::core::AppId id) const;
    std::expected<TestSnapshot, std::string> read_test_snapshot() const;
    std::expected<void, std::string> start_display();
    std::expected<void, std::string> start_test_touch(std::vector<TouchInputStep> steps);
    std::expected<void, std::string> tick_test_touch();
    std::expected<void, std::string> release_test_input();
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
    mutable std::mutex page_navigators_mutex_;
    struct RuntimePages { std::shared_ptr<RuntimePageAdapter> adapter; std::string flow; };
    std::unordered_map<esp_brookesia::system::core::AppId, RuntimePages> runtime_pages_;
    std::shared_ptr<NavigationRequestQueue> runtime_requests_;
    std::unique_ptr<CardRegistry> cards_;
    std::unique_ptr<CardConfigurationStore> card_store_;
    bool card_samples_active_ = false;
    std::unique_ptr<CardSession> card_session_;
    std::shared_ptr<NavigationRequestQueue> card_actions_;
    std::unordered_map<esp_brookesia::system::core::AppId, CardModelFactory> card_factories_;
    uint64_t card_generation_ = 0;
    uint64_t next_card_generation_ = 0;
    esp_brookesia::system::core::AppId card_owner_id_ = esp_brookesia::system::core::INVALID_APP_ID;
    std::optional<CardKey> pending_card_;
    std::shared_ptr<DeveloperMode> developer_mode_;
    std::unique_ptr<InteractionTestAdapter> test_adapter_;
    std::unique_ptr<OwnerSnapshotQueue> test_snapshots_;
    std::unique_ptr<PowerKeyMonitor> power_key_monitor_;
    std::unique_ptr<TestInputQueue> test_power_input_;
    std::unique_ptr<TouchInputSequence> test_touch_input_;
    uint64_t test_touch_foreground_token_ = 0;
    std::atomic_bool cancel_test_touch_ = false;
    std::shared_ptr<std::atomic<uint64_t>> foreground_token_ =
        std::make_shared<std::atomic<uint64_t>>(0);
    esp_brookesia::system::core::AppId shell_id_ = esp_brookesia::system::core::INVALID_APP_ID;
    std::atomic_bool default_back_visible_ = false;
    std::atomic_bool edge_back_enabled_ = false;
    std::atomic_bool edge_back_reserved_ = false;
    std::atomic<esp_brookesia::system::core::AppId> foreground_app_id_{
        esp_brookesia::system::core::INVALID_APP_ID
    };
    uint64_t foreground_generation_ = 0;
    uint32_t display_width_ = 0;
    uint32_t display_height_ = 0;
    uint32_t display_output_id_ = 0;
    std::unique_ptr<semantic::Brightness> brightness_;
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
