#include "espocket/system.hpp"

#include <algorithm>
#include <cinttypes>
#include <utility>
#include <vector>

#include "boost/json/array.hpp"
#include "boost/json/value.hpp"
#include "brookesia/gui_lvgl.hpp"
#include "brookesia/lib_utils/describe_helpers.hpp"
#include "brookesia/service_helper/media/display.hpp"
#include "brookesia/service_manager/helper/base.hpp"
#include "esp_log.h"
#include "espocket/circular_shell.hpp"

namespace espocket {
namespace {

constexpr char TAG[] = "ESPocket.System";
constexpr uint32_t DISPLAY_TIMEOUT_MS = 1000;

using DisplayHelper = esp_brookesia::service::helper::Display;
using DisplaySource = esp_brookesia::gui::lvgl::DisplaySource;

} // namespace

std::expected<void, std::string> System::init()
{
    auto &service_manager = esp_brookesia::service::ServiceManager::get_instance();
    if (!service_manager.init()) {
        return std::unexpected("Failed to initialize ServiceManager");
    }
    if (!service_manager.start()) {
        return std::unexpected("Failed to start ServiceManager");
    }

    auto display_result = start_display();
    if (!display_result) {
        return display_result;
    }

    esp_brookesia::system::core::System::Config config;
    config.gui_backend = std::make_unique<esp_brookesia::gui::lvgl::Backend>();
    config.environment = {
        .width_px = static_cast<int32_t>(display_width_),
        .height_px = static_cast<int32_t>(display_height_),
        .density = 1.0F,
        .font_scale = 1.0F,
        .language = "en",
        .theme_id = "dark",
    };
    config.system_type = "espocket";
    config.start_service_manager = true;
    config.install_registered_apps = false;
    config.install_package_apps = false;

    auto result = esp_brookesia::system::core::System::init(std::move(config));
    if (!result) {
        DisplaySource::get_instance().stop();
        display_binding_.release();
        display_started_ = false;
        return result;
    }
    return {};
}

esp_brookesia::system::core::SystemInfo System::on_get_system_info() const
{
    return {
        .name = "ESPocket",
        .version = "0.1.0",
    };
}

std::expected<void, std::string> System::on_init()
{
    shell_ = std::make_shared<CircularShell>();
    auto result = install_app(shell_);
    if (!result) {
        shell_.reset();
        return std::unexpected("Failed to install Circular Shell: " + result.error());
    }
    shell_id_ = *result;
    ESP_LOGI(TAG, "Circular Shell installed");
    return {};
}

std::expected<void, std::string> System::on_start()
{
    if (shell_id_ == esp_brookesia::system::core::INVALID_APP_ID) {
        return std::unexpected("Circular Shell is not installed");
    }
    auto result = start_app(shell_id_);
    if (!result) {
        return std::unexpected("Failed to start Circular Shell: " + result.error());
    }
    return {};
}

void System::on_deinit()
{
    shell_.reset();
    shell_id_ = esp_brookesia::system::core::INVALID_APP_ID;
    if (display_started_) {
        DisplaySource::get_instance().stop();
        display_started_ = false;
    }
    display_binding_.release();
}

std::expected<void, std::string> System::start_display()
{
    if (!DisplayHelper::is_available()) {
        return std::unexpected("Display service is unavailable");
    }

    auto &service_manager = esp_brookesia::service::ServiceManager::get_instance();
    display_binding_ = service_manager.bind(DisplayHelper::get_name().data());
    if (!display_binding_.is_valid()) {
        return std::unexpected("Failed to bind Display service");
    }

    auto outputs_json = DisplayHelper::call_function_sync<boost::json::array>(
                            DisplayHelper::FunctionId::GetOutputs,
                            esp_brookesia::service::helper::Timeout(DISPLAY_TIMEOUT_MS)
                        );
    if (!outputs_json) {
        return std::unexpected("Failed to get Display outputs: " + outputs_json.error());
    }

    std::vector<DisplayHelper::OutputInfo> outputs;
    if (!BROOKESIA_DESCRIBE_FROM_JSON(boost::json::value(*outputs_json), outputs)) {
        return std::unexpected("Failed to parse Display outputs");
    }
    auto output = std::find_if(outputs.begin(), outputs.end(), [](const auto &candidate) {
        return candidate.width > 0 && candidate.height > 0 && candidate.touch.has_value();
    });
    if (output == outputs.end()) {
        return std::unexpected("No display output with touch support is available");
    }

    // The backlight command shares the panel SPI bus. Complete it before the LVGL worker starts
    // submitting frames so Display and LVGL locks cannot be acquired in opposite orders.
    if (output->backlight.has_value()) {
        auto backlight_result = DisplayHelper::call_function_sync(
                                    DisplayHelper::FunctionId::SetBacklightOnOff,
                                    static_cast<double>(output->id),
                                    true,
                                    esp_brookesia::service::helper::Timeout(DISPLAY_TIMEOUT_MS)
                                );
        if (!backlight_result) {
            return std::unexpected("Failed to turn on Display backlight: " + backlight_result.error());
        }
    }

    esp_brookesia::gui::lvgl::DisplaySourceConfig source_config;
    source_config.output_name = output->name;
    auto &source = DisplaySource::get_instance();
    if (!source.start(source_config)) {
        return std::unexpected("Failed to start LVGL Display source");
    }
    display_started_ = true;

    auto active_result = DisplayHelper::call_function_sync(
                             DisplayHelper::FunctionId::SetActiveSourceRole,
                             output->name,
                             std::string(esp_brookesia::gui::lvgl::DISPLAY_SOURCE_ROLE),
                             esp_brookesia::service::helper::Timeout(DISPLAY_TIMEOUT_MS)
                         );
    if (!active_result) {
        return std::unexpected("Failed to activate LVGL Display source: " + active_result.error());
    }

    display_width_ = output->width;
    display_height_ = output->height;
    ESP_LOGI(
        TAG,
        "Display ready: %s (%" PRIu32 "x%" PRIu32 ")",
        output->name.c_str(),
        display_width_,
        display_height_
    );
    return {};
}

} // namespace espocket
