#pragma once

#include "brookesia/system_core.hpp"
#include "espocket/page_navigator.hpp"

namespace espocket {

struct InstalledPageApp {
    esp_brookesia::system::core::AppId app_id;
    std::shared_ptr<PageNavigator> navigator;
};

std::expected<InstalledPageApp, std::string> install_native_page_app(
    esp_brookesia::system::core::System &core,
    std::shared_ptr<esp_brookesia::system::core::IApp> app,
    PageDeclaration declaration,
    PageNavigator::Presenter presenter
);

} // namespace espocket
