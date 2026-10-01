#include "espocket/developer_mode.hpp"

#include "esp_err.h"
#include "nvs.h"
#include "nvs_flash.h"

namespace espocket {
namespace {

constexpr char STORAGE_NAMESPACE[] = "espocket";
constexpr char STORAGE_KEY[] = "dev_mode";

std::expected<bool, std::string> read_mode()
{
    const auto init = nvs_flash_init();
    if (init != ESP_OK) {
        return std::unexpected(std::string("NVS initialization failed: ") + esp_err_to_name(init));
    }
    nvs_handle_t handle;
    const auto opened = nvs_open(STORAGE_NAMESPACE, NVS_READONLY, &handle);
    if (opened == ESP_ERR_NVS_NOT_FOUND) {
        return false;
    }
    if (opened != ESP_OK) {
        return std::unexpected(std::string("Developer mode read failed: ") + esp_err_to_name(opened));
    }
    uint8_t value = 0;
    const auto read = nvs_get_u8(handle, STORAGE_KEY, &value);
    nvs_close(handle);
    if (read == ESP_ERR_NVS_NOT_FOUND) {
        return false;
    }
    if (read != ESP_OK || value > 1) {
        return std::unexpected("Developer mode value is invalid");
    }
    return value == 1;
}

std::expected<void, std::string> write_mode(bool enabled)
{
    nvs_handle_t handle;
    const auto opened = nvs_open(STORAGE_NAMESPACE, NVS_READWRITE, &handle);
    if (opened != ESP_OK) {
        return std::unexpected(std::string("Developer mode write failed: ") + esp_err_to_name(opened));
    }
    const auto written = nvs_set_u8(handle, STORAGE_KEY, enabled ? 1 : 0);
    const auto committed = written == ESP_OK ? nvs_commit(handle) : written;
    nvs_close(handle);
    if (committed != ESP_OK) {
        return std::unexpected(std::string("Developer mode commit failed: ") + esp_err_to_name(committed));
    }
    return {};
}

} // namespace

std::shared_ptr<DeveloperMode> make_device_developer_mode()
{
    return std::make_shared<DeveloperMode>(read_mode, write_mode);
}

} // namespace espocket
