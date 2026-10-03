#include "shell_internal.hpp"

#include <charconv>

namespace espocket {

// Resolve the registered product palette before acquiring LVGL locks. The
// current GUI applies theme changes to new documents, so this snapshot has the
// same lifetime as the Shell document and owns no separate theme preference.
std::expected<void, std::string> CircularShell::load_theme_colors()
{
    if (!host_.theme_resource) return std::unexpected("Product theme resource is unavailable");
    auto resource = host_.theme_resource(context_->gui().get_theme());
    if (!resource) return std::unexpected(resource.error());
    boost::system::error_code error;
    auto theme = boost::json::parse(*resource, error);
    if (error || !theme.is_object()) return std::unexpected("Invalid product theme resource");
    const auto *assets = theme.as_object().if_contains("assets");
    const boost::json::value *palette = nullptr;
    if (assets && assets->is_array()) {
        for (const auto &asset : assets->as_array()) {
            if (!asset.is_object()) continue;
            const auto *data = asset.as_object().if_contains("data");
            if (data && data->is_object()) palette = data->as_object().if_contains("colors");
            if (palette) break;
        }
    }
    if (!palette || !palette->is_object()) return std::unexpected("Missing product theme palette");
    std::map<std::string, uint32_t, std::less<>> colors;
    for (const auto token : {
        "bg.base", "bg.scrim", "surface.raised", "surface.muted",
        "text.default", "text.muted", "text.subtle", "border.default",
        "primary.fill", "primary.on", "primary.hover", "danger.fill", "danger.on",
    }) {
        const std::string_view path(token);
        const auto separator = path.find('.');
        const auto *group = palette->as_object().if_contains(path.substr(0, separator));
        const auto *value = group && group->is_object() ?
            group->as_object().if_contains(path.substr(separator + 1)) : nullptr;
        if (!value || !value->is_string()) {
            return std::unexpected(std::string("Missing Shell theme color: ") + token);
        }
        const auto &text = value->as_string();
        uint32_t color = 0;
        if (text.size() != 7 || text[0] != '#') {
            return std::unexpected(std::string("Invalid Shell theme color: ") + token);
        }
        const auto parsed = std::from_chars(text.data() + 1, text.data() + text.size(), color, 16);
        if (parsed.ec != std::errc{} || parsed.ptr != text.data() + text.size()) {
            return std::unexpected(std::string("Invalid Shell theme color: ") + token);
        }
        colors.emplace(token, color);
    }
    theme_colors_ = std::move(colors);
    return {};
}

uint32_t CircularShell::theme_color(std::string_view token) const
{
    return theme_colors_.at(std::string(token));
}

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
