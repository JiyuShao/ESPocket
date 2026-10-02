#pragma once

#include <cstdint>
#include <atomic>
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
    std::expected<void, std::string> on_timer(
        esp_brookesia::system::core::AppContext &context,
        esp_brookesia::system::core::TimerId timer_id,
        std::string_view name
    ) override;

private:
    std::weak_ptr<PageNavigator> navigator_;
    esp_brookesia::system::core::AppContext *context_ = nullptr;
    uint32_t count_ = 0;
    struct BackConfirmation {
        std::atomic_bool enabled = false;
        std::atomic<uint64_t> pending_token = 0;
    };
    // The Navigator callback retains confirmation flags, never a raw App pointer.
    std::shared_ptr<BackConfirmation> back_confirmation_ = std::make_shared<BackConfirmation>();
    esp_brookesia::system::core::TimerId back_status_timer_ = 0;
    std::string back_status_;
};

} // namespace espocket
