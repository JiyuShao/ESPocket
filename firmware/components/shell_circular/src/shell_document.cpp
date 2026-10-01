#include "shell_internal.hpp"

namespace espocket {

esp_brookesia::system::core::AppGuiDescriptor CircularShell::get_gui_descriptor() const
{
    return {
        .root_kind = esp_brookesia::system::core::GuiRootKind::JsonString,
        .root = std::string(shell_gui_json_start),
        .resources = {},
        .screen_flows = {
            {
                .screen_flow = std::string(PAGE_FLOW),
                .layer = esp_brookesia::system::core::GuiAppLayer::AppDefault,
            },
            {
                .screen_flow = "overlay_flow",
                .layer = esp_brookesia::system::core::GuiAppLayer::SystemTop,
                .mount_mode = esp_brookesia::gui::MountStackMode::Stack,
            },
        },
    };
}

} // namespace espocket
