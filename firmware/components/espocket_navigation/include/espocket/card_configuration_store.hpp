#pragma once
#include "espocket/card_registry.hpp"
#include <optional>

namespace espocket {
std::expected<CardConfiguration, std::string> decode_card_configuration(std::string_view json);
std::string encode_card_configuration(const CardConfiguration &configuration);

// Serialize calls with registry install/update/uninstall on the App owner task.
// Load/save ports are persistent storage; caller owns the registry and its lifecycle.
class CardConfigurationStore {
public:
    using Load = std::function<std::expected<std::optional<std::string>, std::string>()>;
    using Save = std::function<std::expected<void, std::string>(std::string_view)>;
    CardConfigurationStore(CardRegistry &registry, Load load, Save save);
    std::expected<void, std::string> restore();
    // Validate and persist before publishing. Failed save leaves live configuration intact.
    std::expected<void, std::string> apply(CardConfiguration configuration);
    // Declaration removal is committed by its real Owner first; failure is reported,
    // never converted into successful persistence or a resurrection of an uninstalled App.
    std::expected<void, std::string> save_current();
private:
    CardRegistry &registry_;
    Load load_;
    Save save_;
};
}
