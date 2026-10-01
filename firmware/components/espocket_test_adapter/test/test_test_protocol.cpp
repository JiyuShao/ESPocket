#include <cstdlib>
#include <iostream>
#include <string_view>

#include "espocket/developer_mode.hpp"
#include "espocket/test_protocol.hpp"

void require(bool condition, std::string_view message)
{
    if (!condition) {
        std::cerr << message << '\n';
        std::exit(1);
    }
}

int main()
{
    bool stored = false;
    espocket::DeveloperMode mode(
        [&]() -> std::expected<bool, std::string> { return stored; },
        [&](bool value) -> std::expected<void, std::string> {
            stored = value;
            return {};
        }
    );
    require(mode.restore().has_value() && !mode.enabled(), "developer mode defaults off");
    espocket::TestProtocol protocol(mode, "image-123");
    require(protocol.dispatch(1, "hello").error_code == "developer_mode_off",
            "disabled developer mode rejects USB test commands");
    require(mode.set_enabled(true).has_value() && stored, "enabling persists before exposure");
    auto hello = protocol.dispatch(1, "hello");
    require(hello.ok && hello.image_identity == "image-123" &&
                hello.capabilities.size() == 1 && hello.capabilities[0] == "hello",
            "hello reports the image and only implemented capability");
    require(protocol.dispatch(2, "hello").error_code == "bad_request",
            "unknown protocol version is rejected");
    require(protocol.dispatch(1, "stimulus.touch").error_code == "unsupported",
            "unimplemented stimulus cannot modify product state");
    require(mode.set_enabled(false).has_value() && !stored &&
                protocol.dispatch(1, "hello").error_code == "developer_mode_off",
            "disabling closes the adapter without a reboot");

    auto restored = espocket::DeveloperMode(
        [&]() -> std::expected<bool, std::string> { return stored; },
        [&](bool value) -> std::expected<void, std::string> {
            stored = value;
            return {};
        }
    );
    require(restored.restore().has_value() && !restored.enabled(),
            "persisted disabled state survives a new instance");
}
