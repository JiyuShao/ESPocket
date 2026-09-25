#pragma once

#include <cstdint>
#include <expected>
#include <memory>
#include <string>

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
    void on_deinit() override;

private:
    std::expected<void, std::string> start_display();

    esp_brookesia::service::ServiceBinding display_binding_;
    std::shared_ptr<CircularShell> shell_;
    esp_brookesia::system::core::AppId shell_id_ = esp_brookesia::system::core::INVALID_APP_ID;
    uint32_t display_width_ = 0;
    uint32_t display_height_ = 0;
    bool display_started_ = false;
};

} // namespace espocket
