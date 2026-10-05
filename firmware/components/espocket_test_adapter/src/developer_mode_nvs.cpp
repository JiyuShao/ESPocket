#include "espocket/developer_mode.hpp"

#include "brookesia/service_helper/system/storage.hpp"

namespace espocket {
namespace {

constexpr char STORAGE_NAMESPACE[] = "espocket";
constexpr char STORAGE_KEY[] = "dev_mode";
using Storage = esp_brookesia::service::helper::Storage;

std::expected<bool, std::string> read_mode()
{
    auto entries = Storage::kv_list(STORAGE_NAMESPACE, 5000);
    if (!entries) return std::unexpected(entries.error());
    for (const auto &entry : *entries) {
        if (entry.key == STORAGE_KEY) {
            return Storage::get_key_value<bool>(STORAGE_NAMESPACE, STORAGE_KEY, 5000);
        }
    }
    return false;
}

std::expected<void, std::string> write_mode(bool enabled)
{
    // App Owner callbacks may have a PSRAM stack. Flash IO must execute
    // on Storage's internal-RAM worker. Its Bool backend retains the existing
    // espocket/dev_mode uint8 schema and commits before reporting success.
    return Storage::save_key_value(STORAGE_NAMESPACE, STORAGE_KEY, enabled, 5000);
}

} // namespace

std::shared_ptr<DeveloperMode> make_device_developer_mode()
{
    return std::make_shared<DeveloperMode>(read_mode, write_mode);
}

} // namespace espocket
