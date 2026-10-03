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

} // namespace espocket
