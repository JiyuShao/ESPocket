#include "runtime_navigation_provider.hpp"

namespace espocket {
RuntimeNavigationProvider &RuntimeNavigationProvider::instance()
{
    static RuntimeNavigationProvider provider;
    return provider;
}
void RuntimeNavigationProvider::bind(Handler handler)
{
    std::lock_guard lock(mutex_);
    handler_ = std::move(handler);
}
std::vector<esp_brookesia::runtime::NativeModule> RuntimeNavigationProvider::get_native_modules()
{
    using namespace esp_brookesia::runtime;
    NativeFunctionSpec function;
    function.name = "dispatch";
    function.async_function = [this](const NativeArgs &arguments, NativeAsyncCallback reply) {
        std::lock_guard lock(mutex_);
        if (!handler_) { reply(std::unexpected("system_unavailable")); return; }
        handler_(arguments, std::move(reply));
    };
    return {{"espocketNavigation", {std::move(function)}}};
}
}

BROOKESIA_RUNTIME_FUNCTION_PROVIDER_REGISTER_WITH_SYMBOL(
    espocket::RuntimeNavigationProvider, "ESPocket.Navigation",
    espocket::RuntimeNavigationProvider::instance(), espocket_navigation_provider_registered)
