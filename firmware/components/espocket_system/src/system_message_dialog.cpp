#include "system_internal.hpp"

namespace espocket {

std::expected<void, std::string> System::on_show_message_dialog(
    esp_brookesia::system::core::AppId app_id,
    esp_brookesia::system::core::MessageDialogRequestId request_id,
    const esp_brookesia::system::core::MessageDialogOptions &options)
{
    if (!shell_) return std::unexpected("Circular Shell is unavailable for message dialog");
    return shell_->show_message_dialog(app_id, request_id, options);
}

std::expected<void, std::string> System::on_update_message_dialog(
    esp_brookesia::system::core::AppId app_id,
    esp_brookesia::system::core::MessageDialogRequestId request_id,
    const esp_brookesia::system::core::MessageDialogOptions &options)
{
    if (!shell_) return std::unexpected("Circular Shell is unavailable for message dialog");
    return shell_->update_message_dialog(app_id, request_id, options);
}

void System::on_hide_message_dialog(esp_brookesia::system::core::AppId app_id,
    esp_brookesia::system::core::MessageDialogRequestId request_id)
{
    if (shell_) shell_->hide_message_dialog(app_id, request_id);
}

std::expected<void, std::string> System::on_show_app_loading(esp_brookesia::system::core::AppId app_id)
{
    if (stopping_.load(std::memory_order_acquire) || !shell_) return std::unexpected("System unavailable");
    const auto app = get_app(app_id);
    const auto active = get_active_app();
    if (!app || (app->state != esp_brookesia::system::core::AppState::Starting &&
                 (app->state != esp_brookesia::system::core::AppState::Running ||
                  !active || active->app_id != app_id))) return std::unexpected("Loading owner is not foreground");
    return shell_->show_loading(app_id);
}

void System::on_hide_app_loading(esp_brookesia::system::core::AppId app_id)
{
    if (shell_) shell_->hide_loading(app_id);
}

} // namespace espocket
