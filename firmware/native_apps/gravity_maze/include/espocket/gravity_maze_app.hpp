#pragma once
#include <memory>
#include "brookesia/system_core.hpp"
#include "espocket/gravity_maze_model.hpp"
#include "espocket/imu_source.hpp"
#include "espocket/page_navigator.hpp"

namespace espocket {
class GravityMazeContent;
class GravityMazeApp final : public esp_brookesia::system::core::IApp {
public:
    explicit GravityMazeApp(std::shared_ptr<imu::Source> source = imu::create_board_source());
    ~GravityMazeApp() override;
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
    gravity_maze::Model model_;
    std::shared_ptr<imu::Source> imu_;
    std::shared_ptr<GravityMazeContent> content_;
    esp_brookesia::gui::NativeContentToken mount_;
    esp_brookesia::system::core::TimerId timer_ = 0;
    uint64_t instance_ = 0;
    int64_t last_tick_us_ = 0;
    uint64_t last_sample_timestamp_us_ = 0;
    bool running_ = false;
    bool imu_started_ = false;
};
}
