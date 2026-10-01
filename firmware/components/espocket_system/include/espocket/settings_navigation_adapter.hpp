#pragma once

#include <atomic>
#include <memory>
#include <mutex>

#include "brookesia/system_core.hpp"
#include "espocket/page_navigator.hpp"

namespace espocket {

// Compatibility boundary for official Settings 0.8.3; no product-owned page stack.
class SettingsNavigationAdapter final : public esp_brookesia::system::core::IApp {
public:
    explicit SettingsNavigationAdapter(std::shared_ptr<esp_brookesia::system::core::IApp> app);
    esp_brookesia::system::core::AppManifest get_manifest() const override;
    esp_brookesia::system::core::AppGuiDescriptor get_gui_descriptor() const override;
    std::expected<void, std::string> on_install(esp_brookesia::system::core::AppContext &context) override;
    void on_uninstall(esp_brookesia::system::core::AppContext &context) override;
    std::expected<void, std::string> on_start(esp_brookesia::system::core::AppContext &context) override;
    std::expected<void, std::string> on_pause(esp_brookesia::system::core::AppContext &context) override;
    std::expected<void, std::string> on_resume(esp_brookesia::system::core::AppContext &context) override;
    std::expected<void, std::string> on_stop(esp_brookesia::system::core::AppContext &context) override;
    std::expected<void, std::string> on_action(
        esp_brookesia::system::core::AppContext &context, std::string_view action
    ) override;
    std::expected<void, std::string> on_timer(
        esp_brookesia::system::core::AppContext &context,
        esp_brookesia::system::core::TimerId timer_id, std::string_view name
    ) override;

    std::expected<PageSnapshot, std::string> snapshot() const;
    // Called by Shell's App callback, under Core's shared App callback gate.
    std::expected<void, std::string> request_back();
    // Safe for the raw GUI input callback; never makes a synchronous GUI query.
    bool edge_back_enabled() const;
    void refresh();

private:
    void refresh_availability();
    std::shared_ptr<esp_brookesia::system::core::IApp> app_;
    std::string app_id_;
    esp_brookesia::system::core::AppContext *context_ = nullptr;
    mutable std::recursive_mutex mutex_;
    std::atomic_bool edge_enabled_ = false;
    std::string last_error_;
};

} // namespace espocket
