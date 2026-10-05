#include "system_internal.hpp"

#if CONFIG_ESPOCKET_PACKAGE_ACCEPTANCE_TEST
#include "package_acceptance_inputs.hpp"
#include "brookesia/service_helper/system/storage.hpp"
#include "esp_system.h"
#include <stdexcept>

namespace espocket {
namespace {
using Storage = esp_brookesia::service::helper::Storage;
constexpr char ROOT[] = "/littlefs/.espocket-package-acceptance";
constexpr char APP[] = "espocket.test.store_hello";
constexpr char FLAPPY[] = "brookesia.general.flappy_bird";
constexpr char TAG_ACCEPTANCE[] = "ESPocket.PackageTest";
template<typename Result> Result must(Result result, const char *label)
{
    if (!result) throw std::runtime_error(std::string(label) + ": " + result.error());
    return result;
}
void require(bool value, const char *label)
{
    if (!value) throw std::runtime_error(label);
}
void pass(const char *label) { ESP_LOGI(TAG_ACCEPTANCE, "PASS %s", label); }
}

std::expected<void, std::string> System::prepare_package_acceptance()
try
{
    package_acceptance_original_mode_ = developer_mode_->enabled();
    must(Storage::fs_mkdir(ROOT, 5000), "fixture directory");
    const auto original_path = std::string(ROOT) + "/original-mode";
    if (must(Storage::fs_stat(original_path, 5000), "original mode stat")->exists) {
        auto original = must(Storage::fs_read_text(original_path, 5000), "saved original mode");
        require(*original == "on" || *original == "off", "invalid saved original mode");
        package_acceptance_original_mode_ = *original == "on";
    } else {
        must(Storage::fs_write_text(original_path, package_acceptance_original_mode_ ? "on" : "off", 5000), "save original mode");
    }
    auto marker = must(Storage::fs_stat(std::string(ROOT) + "/phase", 5000), "fixture phase stat");
    if (marker->exists) {
        const auto phase = must(Storage::fs_read_text(std::string(ROOT) + "/phase", 5000), "fixture phase");
        if (*phase == "complete") { package_acceptance_phase_ = 255; return {}; }
        require(*phase == "reboot-on" || *phase == "reboot-off" || *phase == "interrupted-update", "unexpected fixture state");
        if (*phase == "interrupted-update") package_acceptance_phase_ = 11;
        else package_acceptance_rebooted_ = true;
    }
    using namespace acceptance_inputs;
    must(Storage::fs_write(std::string(ROOT) + "/public.pem", esp_brookesia::service::RawBuffer(public_key, sizeof(public_key)), 5000), "public test key");
    must(Storage::fs_write(std::string(ROOT) + "/v1.bpk", esp_brookesia::service::RawBuffer(v1, sizeof(v1)), 5000), "v1 input");
    must(Storage::fs_write(std::string(ROOT) + "/v2.bpk", esp_brookesia::service::RawBuffer(v2, sizeof(v2)), 5000), "v2 input");
    std::vector<uint8_t> corrupted(std::begin(v2), std::end(v2));
    corrupted[corrupted.size() / 2] ^= 1;
    must(Storage::fs_write(std::string(ROOT) + "/corrupt.bpk", esp_brookesia::service::RawBuffer(corrupted.data(), corrupted.size()), 5000), "corrupt input");
    package_acceptance_at_ms_ = static_cast<uint64_t>(esp_timer_get_time() / 1000) + 15'000;
    ESP_LOGW(TAG_ACCEPTANCE, "ISOLATED TEST ONLY: public fixture key, real Core, two controlled resets");
    return {};
}
catch (const std::exception &error) { return std::unexpected(error.what()); }

void System::tick_package_acceptance(uint64_t now_ms)
{
    if (package_acceptance_phase_ == 255 || now_ms < package_acceptance_at_ms_) return;
    package_acceptance_at_ms_ = now_ms + 2000;
    auto find = [this](const char *manifest) -> std::optional<esp_brookesia::system::core::AppInfo> {
        for (const auto &app : list_apps()) if (app.manifest.id == manifest) return app;
        return std::nullopt;
    };
    auto verify = [this, &find](const char *version) {
        auto app = find(APP); require(app.has_value() && app->manifest.version == version, "committed version mismatch");
        auto receipt = must(esp_brookesia::system::core::validate_installed_runtime_package(
            app->manifest.app_path, get_system_type(), runtime_package_policy(), false), "committed receipt");
        require(!receipt->requires_developer() && receipt->signing_key_identity != "unverified", "signed package used developer exception");
        auto paths = must(get_app_storage_paths(app->app_id), "private storage");
        package_acceptance_data_path_ = paths->internal.data + "/acceptance-marker.txt";
        return *app;
    };
    try {
        // Keep PWR assertions on a lit display; a long package transaction
        // can exceed the user's timeout, in which case PWR would only wake.
        if (!display_on_.load()) must(set_display_on(true), "fixture display wake");
        switch (package_acceptance_phase_) {
        case 0: {
            require(!get_active_app() || get_active_app()->app_id == shell_id_, "fixture requires idle Shell");
            if (package_acceptance_rebooted_) {
                auto app = verify("0.2.0");
                require(*must(Storage::fs_read_text(package_acceptance_data_path_, 5000), "reboot private data") == "preserve-me", "private data changed on reboot");
                pass("reboot discovery revalidated signed v2 and private data");
                must(start_app(app.app_id), "reboot v2 start");
                package_acceptance_phase_ = 10;
                return;
            }
            if (auto leftover = find(APP)) {
                require(leftover->manifest.version == "0.1.0" || leftover->manifest.version == "0.2.0", "unknown test version");
                verify(leftover->manifest.version.c_str());
                auto receipt = must(esp_brookesia::system::core::validate_installed_runtime_package(
                    leftover->manifest.app_path, get_system_type(), runtime_package_policy(), false), "owned leftover receipt");
                require(receipt->artifact_sha256 == "7c3f619a4e721d92c74614a2063f884eadf72af82f90bde83f26b61c537aab57" ||
                    receipt->artifact_sha256 == "bfe0887a97929ed618bcc9584417c3cb6cb002d62110e34133357d889d012334", "unknown test artifact");
                require(*must(Storage::fs_read_text(package_acceptance_data_path_, 5000), "owned leftover marker") == "preserve-me", "unknown private marker");
                must(uninstall_app(leftover->app_id), "clean interrupted owned fixture");
                must(Storage::fs_remove(package_acceptance_data_path_, 5000), "clean owned private marker");
                pass("interrupted fixture setup cleaned only validated owned package and marker");
            }
            // Restore the user's pre-acceptance Flappy installation if the
            // preceding Store uninstall removed it. Bind to the exact retained
            // official cache artifact; this is fixture setup, not Store UI evidence.
            if (!find(FLAPPY)) {
                must(developer_mode_->set_enabled(true), "restore developer baseline");
                esp_brookesia::system::core::PackageInstallOptions options;
                options.replace_existing = false;
                options.developer_confirmed = true;
                options.expected_id = FLAPPY;
                options.expected_version = "0.3.0";
                options.expected_sha256 = "ffdf1250f6be38377fe46617b6e0cca196cad4a388f9009edcdf87045165297a";
                must(install_runtime_app_package(
                    "/littlefs/apps/brookesia.general.app_store/cache/apps/brookesia.general.flappy_bird/0.3.0.bpk",
                    options), "restore exact Flappy baseline");
                pass("fixture setup restored exact pre-acceptance Flappy cache package");
            }
            must(developer_mode_->set_enabled(false), "normal mode");
            must(install_runtime_app_package(std::string(ROOT) + "/v1.bpk", false), "signed v1 install");
            auto app = verify("0.1.0");
            must(Storage::fs_write_text(package_acceptance_data_path_, "preserve-me", 5000), "private marker");
            pass("normal-mode signed v1 install and receipt");
            must(start_app(app.app_id), "signed v1 start");
            break;
        }
        case 1: {
            const auto page = must(foreground_page_snapshot(), "v1 page");
            require(page->app_id == APP && page->page_id == "root", "signed v1 foreground mismatch");
            pass("normal-mode signed v1 launch");
            handle_power_short_press();
            require(foreground_token_->load() == 0, "v1 Home failed");
            auto corrupt = install_runtime_app_package(std::string(ROOT) + "/corrupt.bpk", true);
            require(!corrupt, "corrupt update accepted");
            verify("0.1.0");
            pass("corrupt signed update rejected with old receipt retained");
            package_acceptance_fail_update_ = true;
            auto rollback = install_runtime_app_package(std::string(ROOT) + "/v2.bpk", true);
            package_acceptance_fail_update_ = false;
            require(!rollback, "injected activation failure accepted");
            verify("0.1.0");
            require(*must(Storage::fs_read_text(package_acceptance_data_path_, 5000), "rollback private data") == "preserve-me", "rollback private data changed");
            pass("real activation failure rolled back to signed v1 with private data");
            must(Storage::fs_write_text(std::string(ROOT) + "/phase", "interrupted-update", 5000), "interrupted update checkpoint");
            package_acceptance_interrupt_update_ = true;
            must(install_runtime_app_package(std::string(ROOT) + "/v2.bpk", true), "interrupted signed update");
            throw std::runtime_error("interrupted update did not reset");
        }
        case 11: {
            verify("0.1.0");
            require(*must(Storage::fs_read_text(package_acceptance_data_path_, 5000), "recovered private data") == "preserve-me", "interrupted update changed private data");
            pass("reset during pending activation recovered signed v1 and private data");
            must(developer_mode_->set_enabled(false), "normal mode after recovery");
            must(install_runtime_app_package(std::string(ROOT) + "/v2.bpk", true), "signed v2 update");
            auto app = verify("0.2.0");
            require(*must(Storage::fs_read_text(package_acceptance_data_path_, 5000), "update private data") == "preserve-me", "update private data changed");
            pass("normal-mode signed v2 update and private data");
            must(start_app(app.app_id), "signed v2 start");
            package_acceptance_phase_ = 2;
            return;
        }
        case 2: {
            const auto page = must(foreground_page_snapshot(), "v2 page");
            require(page->app_id == APP && page->page_id == "root", "signed v2 foreground mismatch");
            handle_power_short_press();
            pass("normal-mode signed v2 launch and PWR Home");
            must(developer_mode_->set_enabled(true), "enable developer mode");
            auto flappy = find(FLAPPY); require(flappy.has_value(), "Flappy required for developer mode matrix");
            must(start_app(flappy->app_id), "Flappy start before mode off");
            package_acceptance_at_ms_ = now_ms + 10'000;
            break;
        }
        case 3: {
            auto state = must(read_test_snapshot(), "external snapshot");
            require(state->foreground_app_id == FLAPPY && !state->navigation_available && state->page_id.empty(), "external navigation fabricated");
            pass("external legacy App runs without a fabricated Page");
            must(developer_mode_->set_enabled(false), "disable developer mode");
            break;
        }
        case 4: {
            require(foreground_token_->load() == 0 && shell_->current_surface() == ShellSurface::WatchFace, "mode off failed to stop and Home");
            auto flappy = find(FLAPPY); require(flappy.has_value(), "mode off removed installation");
            require(must(Storage::fs_stat(flappy->manifest.app_path + "/.brookesia-install.json", 5000), "retained receipt")->exists, "mode off removed receipt");
            require(!start_app(flappy->app_id), "mode off allowed external start");
            const auto entries = must(project_launcher(*must(launcher_apps("en"), "launcher snapshot"), false), "mode off projection");
            require(std::ranges::none_of(*entries, [](const auto &entry) { return entry.manifest_id == FLAPPY; }), "mode off exposed external Launcher entry");
            pass("mode off stops external App, keeps files, denies start and hides entry");
            must(developer_mode_->set_enabled(true), "re-enable developer mode");
            must(start_app(flappy->app_id), "Flappy restart after mode on");
            package_acceptance_at_ms_ = now_ms + 10'000;
            break;
        }
        case 5: {
            auto state = must(read_test_snapshot(), "reenabled external snapshot");
            require(state->foreground_app_id == FLAPPY && !state->navigation_available, "re-enable did not readmit external App");
            handle_power_short_press();
            require(foreground_token_->load() == 0, "external PWR Home failed");
            pass("mode re-enable readmits external App and PWR Home works");
            must(developer_mode_->set_enabled(package_acceptance_original_mode_), "restore original mode");
            must(Storage::fs_write_text(std::string(ROOT) + "/phase", package_acceptance_original_mode_ ? "reboot-on" : "reboot-off", 5000), "reboot checkpoint");
            ESP_LOGI(TAG_ACCEPTANCE, "CHECKPOINT controlled reboot after committed signed v2");
            package_acceptance_phase_ = 254;
            package_acceptance_at_ms_ = now_ms + 5000;
            return;
        }
        case 254: esp_restart(); return;
        case 10: {
            const auto page = must(foreground_page_snapshot(), "reboot page");
            require(page->app_id == APP && page->page_id == "root", "reboot launch mismatch");
            handle_power_short_press();
            auto app = verify("0.2.0");
            const auto path = app.manifest.app_path;
            must(uninstall_app(app.app_id), "signed v2 uninstall");
            require(!find(APP) && !must(Storage::fs_stat(path + "/.brookesia-install.json", 5000), "removed receipt")->exists &&
                !must(Storage::fs_stat(path + "/.brookesia-package.bpk", 5000), "removed retained archive")->exists, "uninstall retained committed package");
            pass("reboot launch, uninstall, receipt and retained archive removal");
            if (must(Storage::fs_stat(package_acceptance_data_path_, 5000), "owned private marker stat")->exists)
                must(Storage::fs_remove(package_acceptance_data_path_, 5000), "remove owned private marker");
            for (const char *file : {"v1.bpk", "v2.bpk", "corrupt.bpk", "public.pem"})
                must(Storage::fs_remove(std::string(ROOT) + "/" + file, 5000), "fixture input cleanup");
            must(developer_mode_->set_enabled(package_acceptance_original_mode_), "final mode restore");
            must(Storage::fs_write_text(std::string(ROOT) + "/phase", "complete", 5000), "completion marker");
            pass("COMPLETE test artifacts removed and original Developer Mode restored");
            package_acceptance_phase_ = 255;
            return;
        }
        default: throw std::runtime_error("invalid fixture phase");
        }
        ++package_acceptance_phase_;
    } catch (const std::exception &error) {
        package_acceptance_fail_update_ = false;
        package_acceptance_interrupt_update_ = false;
        package_acceptance_phase_ = 255;
        auto restored = developer_mode_->set_enabled(package_acceptance_original_mode_);
        ESP_LOGE(TAG_ACCEPTANCE, "FAIL %s; original mode restored=%s", error.what(), restored ? "yes" : "no");
    }
}
} // namespace espocket
#else
namespace espocket {
std::expected<void, std::string> System::prepare_package_acceptance() { return {}; }
void System::tick_package_acceptance(uint64_t) {}
}
#endif
