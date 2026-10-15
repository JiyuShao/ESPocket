#pragma once

#include <memory>
#include "brookesia/system_core.hpp"
#include "espocket/imu_source.hpp"
#include "espocket/mouse_endpoint.hpp"
#include "espocket/mouse_model.hpp"
#include "espocket/page_navigator.hpp"

namespace espocket {
class BleRemoteContent;
class BleRemoteApp final : public esp_brookesia::system::core::IApp {
public:
    BleRemoteApp(std::shared_ptr<hid::Endpoint> endpoint = hid::create_board_endpoint(),
                 std::shared_ptr<imu::Source> imu_source = imu::create_board_source());
    ~BleRemoteApp() override;
    PageDeclaration get_page_declaration() const;
    bool present_page(std::string_view from, std::string_view to) const;
    esp_brookesia::system::core::AppManifest get_manifest() const override;
    esp_brookesia::system::core::AppGuiDescriptor get_gui_descriptor() const override;
    std::expected<void, std::string> on_start(esp_brookesia::system::core::AppContext &) override;
    std::expected<void, std::string> on_stop(esp_brookesia::system::core::AppContext &) override;
    std::expected<void, std::string> on_pause(esp_brookesia::system::core::AppContext &) override;
    std::expected<void, std::string> on_resume(esp_brookesia::system::core::AppContext &) override;
    std::expected<void, std::string> on_timer(esp_brookesia::system::core::AppContext &, esp_brookesia::system::core::TimerId, std::string_view) override;
private:
    void try_start();
    hid::MouseModel model_;
    std::shared_ptr<hid::Endpoint> endpoint_;
    std::shared_ptr<imu::Source> imu_;
    std::shared_ptr<BleRemoteContent> content_;
    esp_brookesia::gui::NativeContentToken mount_;
    esp_brookesia::system::core::TimerId timer_ = 0;
    uint64_t instance_ = 0;
    int64_t last_tick_us_ = 0;
    uint32_t retry_ms_ = 0;
    uint32_t last_sequence_ = 0;
    bool running_ = false, endpoint_started_ = false, imu_started_ = false, last_points_empty_ = true;
};
}
