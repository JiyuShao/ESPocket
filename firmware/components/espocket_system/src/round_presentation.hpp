#pragma once

#include <algorithm>
#include <cmath>
#include "brookesia/system_core/system/system.hpp"
#include "round_resources.hpp"

namespace espocket {
inline esp_brookesia::system::core::System::Config::AppPresentation round_app_presentation(
    const esp_brookesia::system::core::AppManifest &manifest,
    const esp_brookesia::gui::Environment &environment)
{
    using namespace esp_brookesia;
    system::core::System::Config::AppPresentation result{environment, {}};
    if (manifest.kind != system::core::AppKind::Runtime ||
            std::find(manifest.supported_systems.begin(), manifest.supported_systems.end(), "espocket") != manifest.supported_systems.end()) return result;
    const auto diameter = std::min(environment.width_px, environment.height_px);
    if (diameter <= 0) return result;
    const bool chat = manifest.id == "brookesia.general.ai_chatbot" && manifest.version == "0.2.1";
    const bool calculator = manifest.id == "brookesia.general.calculator" && manifest.version == "0.3.0";
    if (chat || calculator) {
        result.environment.width_px = diameter;
        result.environment.height_px = diameter;
        result.environment.density = static_cast<float>(diameter) / 466.0F;
        result.root_document = chat ? chat_round_document() : calculator_round_document();
        return result;
    }
    const auto side = static_cast<int32_t>(std::floor(diameter / std::sqrt(2.0)));
    const auto height = side;
    result.environment.width_px = side;
    result.environment.height_px = height;
    result.environment.density = static_cast<float>(side) / 480.0F;
    result.viewport = gui::GuiViewport{
        (environment.width_px - side) / 2, (environment.height_px - height) / 2, side, height
    };
    return result;
}
}
