#pragma once

#include <atomic>
#include <cstdint>
#include <expected>
#include <memory>
#include <string>
#include <string_view>

#include "brookesia/service_manager/service/manager.hpp"
#include "brookesia/system_core.hpp"

namespace espocket {

class CircularShell;

class System final : public esp_brookesia::system::core::System {
public:
    std::expected<void, std::string> init();

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
    void handle_home_intent(uint64_t foreground_token);
    void clear_foreground(const esp_brookesia::system::core::AppInfo &app);
    void restore_launcher_after_lifecycle(const esp_brookesia::system::core::AppInfo &app);

    esp_brookesia::service::ServiceBinding display_binding_;
    std::shared_ptr<CircularShell> shell_;
    std::shared_ptr<std::atomic<uint64_t>> foreground_token_ =
        std::make_shared<std::atomic<uint64_t>>(0);
    esp_brookesia::system::core::AppId shell_id_ = esp_brookesia::system::core::INVALID_APP_ID;
    std::atomic<esp_brookesia::system::core::AppId> foreground_app_id_{
        esp_brookesia::system::core::INVALID_APP_ID
    };
    uint64_t foreground_generation_ = 0;
    uint32_t display_width_ = 0;
    uint32_t display_height_ = 0;
    bool display_started_ = false;
    std::atomic_bool stopping_ = false;
    std::atomic_bool runtime_stop_failed_ = false;
};

} // namespace espocket
