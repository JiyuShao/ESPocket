#include "system_internal.hpp"
#include "espocket/reset_resume_checkpoint.hpp"
#include "brookesia/service_helper/system/storage.hpp"
#include "esp_system.h"

namespace espocket {
namespace {
using Storage = esp_brookesia::service::helper::Storage;
constexpr char RESUME_NAMESPACE[] = "espocket";
constexpr char RESUME_KEY[] = "reset_app_v1";

std::expected<std::string, std::string> load_reset_target()
{
    auto binding = esp_brookesia::service::ServiceManager::get_instance().bind(Storage::get_name().data());
    if (!binding.is_valid()) return std::unexpected("reset_storage_unavailable");
    auto values = Storage::call_function_sync<boost::json::object>(
        Storage::FunctionId::KVGet, std::string(RESUME_NAMESPACE), boost::json::array{RESUME_KEY},
        esp_brookesia::service::helper::Timeout(5000));
    if (!values) return std::unexpected(values.error());
    const auto entry = values->find(RESUME_KEY);
    if (entry == values->end()) return std::string{};
    if (!entry->value().is_string() || entry->value().as_string().size() > 192)
        return std::unexpected("invalid_reset_checkpoint");
    return std::string(entry->value().as_string());
}

std::expected<void, std::string> save_reset_target(std::string_view id)
{
    auto binding = esp_brookesia::service::ServiceManager::get_instance().bind(Storage::get_name().data());
    if (!binding.is_valid()) return std::unexpected("reset_storage_unavailable");
    auto saved = Storage::call_function_sync(Storage::FunctionId::KVSet, std::string(RESUME_NAMESPACE),
        boost::json::object{{RESUME_KEY, std::string(id)}}, esp_brookesia::service::helper::Timeout(5000));
    if (!saved) return std::unexpected(saved.error());
    return {};
}
}

void System::init_reset_resume()
{
    reset_resume_ = std::make_unique<ResetResumeCheckpoint>(load_reset_target, save_reset_target);
}

void System::remember_reset_resume(const esp_brookesia::system::core::AppInfo &app)
{
    if (!reset_resume_) return;
    const auto id = reset_resume_apps_.contains(app.app_id) ? std::string_view(app.manifest.id) : std::string_view{};
    if (auto saved = reset_resume_->remember(id); !saved)
        ESP_LOGW(TAG, "Hardware reset recovery checkpoint failed: %s", saved.error().c_str());
}

void System::clear_reset_resume()
{
    if (reset_resume_) {
        if (auto saved = reset_resume_->remember(""); !saved)
            ESP_LOGW(TAG, "Hardware reset recovery clear failed: %s", saved.error().c_str());
    }
}

void System::restore_after_hardware_reset()
{
    if (!reset_resume_) return;
    const auto reason = esp_reset_reason();
    // EN Reset and a cold power-on are indistinguishable on this board.
    // Panic/watchdog/software reboot never automatically reopens a recording App.
    const bool hardware = reason == ESP_RST_POWERON || reason == ESP_RST_EXT || reason == ESP_RST_USB;
    auto target = reset_resume_->consume(hardware);
    if (!target) {
        ESP_LOGW(TAG, "Hardware reset recovery unavailable: %s", target.error().c_str());
        return;
    }
    if (target->empty()) return;
    const auto apps = list_apps();
    const auto app = std::ranges::find_if(apps, [&](const auto &candidate) {
        return candidate.manifest.id == *target && candidate.manifest.visible &&
               reset_resume_apps_.contains(candidate.app_id);
    });
    if (app == apps.end()) return;
    auto started = start_app(app->app_id); // Normal Core package trust and lifecycle remain authoritative.
    if (!started) ESP_LOGW(TAG, "Hardware reset App recovery failed: %s", started.error().c_str());
    else ESP_LOGI(TAG, "Hardware reset App restored: %s", app->manifest.id.c_str());
}

} // namespace espocket
