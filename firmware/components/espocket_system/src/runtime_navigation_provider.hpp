#pragma once
#include "brookesia/runtime_manager/function_bridge.hpp"
#include <mutex>

namespace espocket {
// Binding is removed under the same lock before System destruction.
class RuntimeNavigationProvider final : public esp_brookesia::runtime::RuntimeFunctionProvider {
public:
    using Handler = esp_brookesia::runtime::NativeAsyncFunction;
    static RuntimeNavigationProvider &instance();
    void bind(Handler handler);
    std::vector<esp_brookesia::runtime::NativeModule> get_native_modules() override;
private:
    std::mutex mutex_;
    Handler handler_;
};
}
