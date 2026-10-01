#pragma once

#include <cstdint>
#include <expected>
#include <memory>
#include <string>
#include <string_view>

#include "brookesia/system_core.hpp"

namespace espocket {

class PageNavigator;
struct PageDeclaration;

class HelloApp final : public esp_brookesia::system::core::IApp {
public:
    PageDeclaration get_page_declaration() const;
    void set_navigator(std::weak_ptr<PageNavigator> navigator);
    bool present_page(std::string_view from, std::string_view to);
    esp_brookesia::system::core::AppManifest get_manifest() const override;
    esp_brookesia::system::core::AppGuiDescriptor get_gui_descriptor() const override;

    std::expected<void, std::string> on_start(
        esp_brookesia::system::core::AppContext &context
    ) override;
    std::expected<void, std::string> on_stop(
        esp_brookesia::system::core::AppContext &context
    ) override;
    std::expected<void, std::string> on_action(
        esp_brookesia::system::core::AppContext &context,
        std::string_view action
    ) override;

private:
    std::weak_ptr<PageNavigator> navigator_;
    esp_brookesia::system::core::AppContext *context_ = nullptr;
    uint32_t count_ = 0;
};

} // namespace espocket
