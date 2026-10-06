#include "system_internal.hpp"
#include "brookesia/lib_utils/function_guard.hpp"
#include "esp_lv_adapter.h"
#include "lvgl.h"

namespace espocket {

std::expected<void, std::string> System::set_display_on(bool on)
{
    if (!shell_) {
        return std::unexpected("Circular Shell is unavailable");
    }
    if (display_on_.load(std::memory_order_acquire) == on) {
        return {};
    }

    if (!on) {
        auto active = get_active_app();
        resume_app_id_ = active.has_value() && active->app_id != shell_id_ && active->manifest.visible ?
                         active->app_id : esp_brookesia::system::core::INVALID_APP_ID;
        auto input_result = shell_->set_display_on(false);
        if (!input_result) {
            return input_result;
        }
    }

    auto backlight_result = DisplayHelper::call_function_sync(
                                DisplayHelper::FunctionId::SetBacklightOnOff,
                                static_cast<double>(display_output_id_),
                                on,
                                esp_brookesia::service::helper::Timeout(DISPLAY_TIMEOUT_MS)
                            );
    if (!backlight_result) {
        if (!on) {
            (void)shell_->set_display_on(true);
        }
        return std::unexpected("Failed to change display power: " + backlight_result.error());
    }

    if (on) {
        auto input_result = shell_->set_display_on(true);
        if (!input_result) {
            return input_result;
        }
    }
    display_on_.store(on, std::memory_order_release);
    if (!on) pause_card();
    else if (foreground_token_->load() == 0 &&
        (shell_->current_surface() == ShellSurface::LeftAppCard || shell_->current_surface() == ShellSurface::RightAppCard)) {
        if (auto resumed = resume_card(); !resumed) {
            ESP_LOGW(TAG, "Card wake presentation failed: %s", resumed.error().c_str());
        }
    }
    ESP_LOGI(TAG, "M6 display state: %s", on ? "On" : "Off");
    return {};
}

void System::report_startup_failure(std::string_view reason)
{
    startup_failed_ = true;
    stopping_.store(true, std::memory_order_release);
    ESP_LOGE(TAG, "Critical startup failure; explicit device restart required: %.*s",
             static_cast<int>(reason.size()), reason.data());
    // Core has already unwound. This source is held only for the fatal diagnostic,
    // until explicit device restart/destruction; no Shell/App execution is resumed.
    if (!display_started_) {
        auto display = start_display();
        if (!display) {
            ESP_LOGE(TAG, "Fatal diagnostic display unavailable: %s", display.error().c_str());
            return;
        }
    }
    if (esp_lv_adapter_lock(1000) != ESP_OK) {
        ESP_LOGE(TAG, "Fatal diagnostic GUI lock unavailable");
        stop_display();
        return;
    }
    bool shown = false;
    if (auto *screen = lv_screen_active()) {
        lv_obj_clean(screen);
        lv_obj_set_style_bg_color(screen, lv_color_hex(0x101820), 0);
        if (auto *label = lv_label_create(screen)) {
            lv_obj_set_width(label, static_cast<int32_t>(display_width_ * 3 / 4));
            lv_obj_set_style_text_align(label, LV_TEXT_ALIGN_CENTER, 0);
            lv_obj_set_style_text_color(label, lv_color_hex(0xFFFFFF), 0);
            lv_label_set_text(label, "Startup failed\nRestart device");
            lv_obj_center(label);
            shown = true;
        }
    }
    esp_lv_adapter_unlock();
    if (!shown) {
        ESP_LOGE(TAG, "Fatal diagnostic GUI allocation unavailable");
        stop_display();
    }
}

void System::stop_display()
{
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

    esp_brookesia::lib_utils::FunctionGuard cleanup([this]() { stop_display(); });

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
    source_config.buffer_height = 24;
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
    display_output_id_ = output->id;
    // One selected output, reached only through the public Display service.
    brightness_ = std::make_unique<semantic::Brightness>(output->name,
        [id = output->id]() {
            return DisplayHelper::call_function_sync<double>(
                DisplayHelper::FunctionId::GetBacklightBrightness, static_cast<double>(id),
                esp_brookesia::service::helper::Timeout(DISPLAY_TIMEOUT_MS));
        },
        [id = output->id](double percent) {
            return DisplayHelper::call_function_sync<void>(
                DisplayHelper::FunctionId::SetBacklightBrightness, static_cast<double>(id), percent,
                esp_brookesia::service::helper::Timeout(DISPLAY_TIMEOUT_MS));
        },
        [this](const semantic::Access& access) {
            // Only the internally composed Shell caller is admitted in this slice.
            // Assistant stays denied until confirmed user-goal admission is wired.
            const bool ui = access.caller.kind == semantic::CallerKind::ProductUi &&
                            access.caller.id == "espocket.shell" && access.caller.running_instance == 0;
            const bool available = !stopping_.load(std::memory_order_acquire) &&
                                   display_binding_.is_valid() && DisplayHelper::is_available();
            return semantic::Permission{ui, available, available};
        });
    cleanup.release();
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
