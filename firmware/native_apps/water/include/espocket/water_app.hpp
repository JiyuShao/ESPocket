#pragma once
#include "brookesia/system_core.hpp"
#include "espocket/page_navigator.hpp"
#include "espocket/water_input.hpp"
namespace espocket {
class WaterContent;
namespace water { class Worker; }
class WaterApp final : public esp_brookesia::system::core::IApp {
public:
    WaterApp();
    ~WaterApp() override;
    PageDeclaration get_page_declaration() const;
    bool present_page(std::string_view from, std::string_view to) const;
    esp_brookesia::system::core::AppManifest get_manifest() const override;
    esp_brookesia::system::core::AppGuiDescriptor get_gui_descriptor() const override;
    std::expected<void, std::string> on_start(esp_brookesia::system::core::AppContext &) override;
    std::expected<void, std::string> on_stop(esp_brookesia::system::core::AppContext &) override;
    std::expected<void, std::string> on_pause(esp_brookesia::system::core::AppContext &) override;
    std::expected<void, std::string> on_resume(esp_brookesia::system::core::AppContext &) override;
    std::expected<void, std::string> on_timer(esp_brookesia::system::core::AppContext &,
        esp_brookesia::system::core::TimerId, std::string_view) override;
private:
    water::Input input_;
    std::shared_ptr<WaterContent> content_;
    std::unique_ptr<water::Worker> worker_;
    esp_brookesia::gui::NativeContentToken mount_;
    esp_brookesia::system::core::TimerId timer_ = 0;
    uint64_t instance_ = 0;
    bool running_ = false, has_frame_ = false, failed_ = false;
    uint32_t last_sequence_ = 0;
};
}
