#include "espocket/native_page_installation.hpp"

namespace espocket {

std::expected<InstalledPageApp, std::string> install_native_page_app(
    esp_brookesia::system::core::System &core,
    std::shared_ptr<esp_brookesia::system::core::IApp> app,
    PageDeclaration declaration,
    PageNavigator::Presenter presenter
)
{
    if (!app || declaration.app_id != app->get_manifest().id) {
        return std::unexpected("page_manifest_identity_mismatch");
    }
    auto navigator = PageNavigator::create(std::move(declaration), std::move(presenter));
    if (!navigator) {
        return std::unexpected("invalid_page_declaration");
    }
    auto shared_navigator = std::make_shared<PageNavigator>(std::move(*navigator));
    auto installed = core.install_app(std::move(app));
    if (!installed) {
        return std::unexpected(installed.error());
    }
    return InstalledPageApp{*installed, std::move(shared_navigator)};
}

} // namespace espocket
