#include "espocket/launcher_projection.hpp"
#include "espocket/launcher_pages.hpp"
#include <array>
#include <algorithm>
#include <atomic>
#include <functional>
#include <map>
#include <mutex>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>
#include <cstdint>

inline int64_t test_clock_us = 0;
inline int64_t esp_timer_get_time() { return test_clock_us; }
#define ESP_LOGW(...) ((void)0)
#define ESP_LOGI(...) ((void)0)
namespace esp_brookesia::gui {
struct BindingValueUpdate { std::string path, key, value; };
}
namespace espocket {
constexpr char LAUNCHER_TAG[] = "test";
enum class ShellSurface { WatchFace, Launcher };
struct FakeGui {
    std::map<std::string, bool> regions;
    std::map<std::string, int> image_leases;
    std::set<std::string> unavailable_icons;
    std::string fail;
    std::map<std::string, std::string> bindings;
    int preparations = 0;
    bool fixed_available = true;
    mutable int language_reads = 0;
    std::string get_language() const { ++language_reads; return "en"; }
    std::expected<void, std::string> create_view(const char *type, const std::string &parent, const std::string &instance) {
        ++preparations;
        if (fail == type) return std::unexpected("injected create failure");
        if (std::string(type) == "launcher_region") regions[parent + "/" + instance] = true;
        return {};
    }
    std::expected<void, std::string> set_text(const std::string &, const std::string &) {
        return fail == "text" ? std::expected<void,std::string>(std::unexpected("text failure")) : std::expected<void,std::string>{};
    }
    std::expected<void, std::string> preload_image(const std::string &image) {
        if (unavailable_icons.contains(image)) return std::unexpected("missing icon");
        ++image_leases[image]; return {};
    }
    std::expected<void, std::string> release_preloaded_image(const std::string &image) {
        if (--image_leases[image] < 0) throw std::runtime_error("image double release");
        return {};
    }
    std::expected<void, std::string> set_binding_values(const std::vector<esp_brookesia::gui::BindingValueUpdate> &updates) {
        for (const auto &update : updates) {
            if ((fail == "bindings" && update.key == "src") || (fail == "swap" && update.value == "false"))
                return std::unexpected("binding failure");
        }
        for (const auto &update : updates) {
            bindings[update.path + ":" + update.key] = update.value;
            if (regions.contains(update.path) && update.key == "hidden") regions[update.path] = update.value == "true";
        }
        return {};
    }
    std::expected<void, std::string> set_binding_value(const std::string &, const char *, const char *) { return {}; }
    std::expected<void, std::string> destroy_view(const std::string &path) {
        if (!regions.erase(path)) { fixed_available = false; return std::unexpected("wrong destruction scope"); }
        return {};
    }
};
struct FakeContext { FakeGui view; FakeGui &gui() { return view; } };
struct FakeConnection { void disconnect() {} };
struct FakeGesture { std::atomic<bool> modal_active{false}; std::atomic<int> launcher_pull_distance{0}, launcher_return_threshold{100}, launcher_scroll_top{0}; };
struct FakeHost {
    std::function<std::expected<std::vector<LauncherApp>, std::string>(std::string_view)> launcher_apps;
    std::function<uint64_t()> launcher_generation;
    struct { std::function<bool()> enabled; } developer_mode;
    std::function<bool()> app_visible;
};
class CircularShell {
public:
    void refresh_launcher(); void dispatch_launcher(); void stop_launcher();
    std::expected<void,std::string> show_launcher_page(size_t requested);
    ShellSurface current_surface() { return ShellSurface::Launcher; }
    std::expected<void,std::string> open_app(const std::string &id, const std::string &) { opened.push_back(id); return {}; }
    void set_status_text(const char *, const std::string &) {}
    FakeContext *context_ = nullptr; FakeHost host_;
    int64_t launcher_refresh_at_us_ = 0;
    size_t launcher_page_ = 0;
    uint64_t launcher_generation_ = UINT64_MAX, launcher_view_generation_ = 0;
    bool launcher_developer_enabled_ = false;
    std::string launcher_language_, launcher_region_, launcher_intent_;
    std::vector<LauncherEntry> launcher_entries_;
    std::vector<std::string> launcher_images_, opened;
    std::mutex launcher_intent_mutex_;
    std::optional<FakeGesture> home_gesture_state_;
    FakeConnection launcher_connection_;
};
}
