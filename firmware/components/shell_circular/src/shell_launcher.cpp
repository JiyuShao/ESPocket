#include "shell_internal.hpp"

namespace espocket {

void CircularShell::refresh_launcher()
{
    if (!context_ || !host_.launcher_apps) return;
    const auto now = esp_timer_get_time();
    const bool developer = host_.developer_mode.enabled && host_.developer_mode.enabled();
    const auto generation = host_.launcher_generation ? host_.launcher_generation() : 0;
    const auto language = context_->gui().get_language();
    const bool changed = generation != launcher_generation_ || developer != launcher_developer_enabled_ ||
                         language != launcher_language_;
    if (now < launcher_refresh_at_us_ && !changed) return;
    // Full reconciliation also recovers notifications that were merged or missed.
    launcher_refresh_at_us_ = now + 5'000'000;
    // A failed preparation also consumes this generation. Retry on the full
    // reconciliation interval, or immediately when a genuinely new change arrives.
    launcher_generation_ = generation;
    launcher_developer_enabled_ = developer;
    launcher_language_ = language;
    auto apps = host_.launcher_apps(language);
    auto projected = apps ? project_launcher(*apps, developer) :
        std::expected<std::vector<LauncherEntry>, std::string>(std::unexpected(apps.error()));
    if (!projected) {
        ESP_LOGW(LAUNCHER_TAG, "Reconciliation failed: %s", projected.error().c_str());
        launcher_generation_ = generation;
        launcher_developer_enabled_ = developer;
        launcher_language_ = language;
        return;
    }
    if (*projected == launcher_entries_ && !launcher_region_.empty()) {
        launcher_generation_ = generation;
        launcher_developer_enabled_ = developer;
        launcher_language_ = language;
        return;
    }
    const auto region = "/launcher/dynamic_" + std::to_string(++launcher_view_generation_);
    auto created = context_->gui().create_view("launcher_region", "/launcher", region.substr(10));
    if (!created) { ESP_LOGW(LAUNCHER_TAG, "Cannot prepare Launcher: %s", created.error().c_str()); return; }
    std::vector<std::string> images;
    bool ready = true;
    for (const auto &entry : *projected) {
        const auto path = region + "/" + entry.instance;
        auto row = context_->gui().create_view("launcher_item", region, entry.instance);
        if (!row || !context_->gui().set_text(path + "/label", entry.name)) { ready = false; break; }
        bool icon_ready = !entry.icon.empty() && context_->gui().preload_image(entry.icon).has_value();
        if (icon_ready) images.push_back(entry.icon);
        auto updates = std::vector<esp_brookesia::gui::BindingValueUpdate>{
            {path + "/icon", "src", icon_ready ? entry.icon : ""},
            {path + "/icon", "hidden", icon_ready ? "false" : "true"},
            {path + "/label", "left", icon_ready ? "64dp" : "22dp"},
        };
        if (!context_->gui().set_binding_values(updates)) { ready = false; break; }
    }
    if (ready) {
        std::vector<esp_brookesia::gui::BindingValueUpdate> visibility{{region, "hidden", "false"}};
        if (!launcher_region_.empty()) visibility.push_back({launcher_region_, "hidden", "true"});
        // Public batch holds the GUI lock for the swap: prepared rows appear together.
        ready = context_->gui().set_binding_values(visibility).has_value();
    }
    if (!ready) {
        (void)context_->gui().destroy_view(region);
        for (const auto &image : images) (void)context_->gui().release_preloaded_image(image);
        ESP_LOGW(LAUNCHER_TAG, "Launcher replacement failed; retaining complete previous view");
        launcher_generation_ = generation;
        launcher_developer_enabled_ = developer;
        launcher_language_ = language;
        return;
    }
    if (!launcher_region_.empty()) (void)context_->gui().destroy_view(launcher_region_);
    for (const auto &image : launcher_images_) (void)context_->gui().release_preloaded_image(image);
    launcher_region_ = region;
    launcher_entries_ = std::move(*projected);
    launcher_images_ = std::move(images);
    launcher_generation_ = generation;
    launcher_developer_enabled_ = developer;
    launcher_language_ = language;
    ESP_LOGI(LAUNCHER_TAG, "Reconciled %u dynamic App entries", static_cast<unsigned>(launcher_entries_.size()));
}

void CircularShell::dispatch_launcher()
{
    std::string path;
    { std::lock_guard lock(launcher_intent_mutex_); path.swap(launcher_intent_); }
    if (path.empty() || !context_ || current_surface() != ShellSurface::Launcher ||
            (host_.app_visible && host_.app_visible()) ||
            (home_gesture_state_ && (home_gesture_state_->modal_active.load() ||
                home_gesture_state_->launcher_pull_distance.load() >= home_gesture_state_->launcher_return_threshold.load()))) return;
    const auto found = std::ranges::find_if(launcher_entries_, [&](const auto &entry) {
        return path == launcher_region_ + "/" + entry.instance;
    });
    if (found == launcher_entries_.end()) return; // Retired view or removed target.
    auto apps = host_.launcher_apps(context_->gui().get_language());
    const bool developer = host_.developer_mode.enabled && host_.developer_mode.enabled();
    const auto target = apps ? resolve_launcher_target(*apps, found->manifest_id, developer) :
        std::expected<uint32_t, std::string>(std::unexpected(apps.error()));
    const auto result = target ? open_app(found->manifest_id, found->name) :
        std::expected<void, std::string>(std::unexpected(target.error()));
    if (!result) {
        ESP_LOGW(LAUNCHER_TAG, "Launch rejected: %s", result.error().c_str());
        set_status_text("/launcher/launch_status", "Unable to open " + found->name);
        (void)context_->gui().set_binding_value("/launcher/launch_status", "hidden", "false");
        launcher_refresh_at_us_ = 0;
    } else {
        set_status_text("/launcher/launch_status", "");
        (void)context_->gui().set_binding_value("/launcher/launch_status", "hidden", "true");
    }
}

void CircularShell::stop_launcher()
{
    launcher_connection_.disconnect();
    if (context_ && !launcher_region_.empty()) (void)context_->gui().destroy_view(launcher_region_);
    if (context_) for (const auto &image : launcher_images_) (void)context_->gui().release_preloaded_image(image);
    launcher_images_.clear();
    launcher_entries_.clear();
    launcher_region_.clear();
    std::lock_guard lock(launcher_intent_mutex_);
    launcher_intent_.clear();
}
} // namespace espocket
