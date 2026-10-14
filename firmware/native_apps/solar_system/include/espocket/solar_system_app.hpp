#pragma once
#include "brookesia/system_core.hpp"
#include "espocket/page_navigator.hpp"
#include "espocket/orbit_input.hpp"
namespace espocket {
class OrbitContent;
namespace orbit { class Worker; }
class SolarSystemApp final : public esp_brookesia::system::core::IApp {
public:
    SolarSystemApp();
    ~SolarSystemApp() override;
    PageDeclaration get_page_declaration() const;
    void set_navigator(std::weak_ptr<PageNavigator>);
    bool present_page(std::string_view from, std::string_view to);
    esp_brookesia::system::core::AppManifest get_manifest() const override;
    esp_brookesia::system::core::AppGuiDescriptor get_gui_descriptor() const override;
    std::expected<void, std::string> on_start(esp_brookesia::system::core::AppContext &) override;
    std::expected<void, std::string> on_stop(esp_brookesia::system::core::AppContext &) override;
    std::expected<void, std::string> on_pause(esp_brookesia::system::core::AppContext &) override;
    std::expected<void, std::string> on_resume(esp_brookesia::system::core::AppContext &) override;
    std::expected<void, std::string> on_timer(esp_brookesia::system::core::AppContext &,
        esp_brookesia::system::core::TimerId, std::string_view) override;
private:
    orbit::Input input_;
    orbit::Motion motion_;
    orbit::Kind selected_ = orbit::Kind::Moon;
    std::shared_ptr<OrbitContent> content_;
    std::unique_ptr<orbit::Worker> worker_;
    std::weak_ptr<PageNavigator> navigator_;
    esp_brookesia::system::core::AppContext *context_ = nullptr;
    esp_brookesia::gui::NativeContentToken mount_;
    esp_brookesia::system::core::TimerId timer_ = 0;
    uint64_t instance_ = 0, last_ms_ = 0;
    bool running_ = false, viewer_ = false, failed_ = false;
};
}
