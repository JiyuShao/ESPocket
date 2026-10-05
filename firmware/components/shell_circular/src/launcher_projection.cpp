#include "espocket/launcher_projection.hpp"

#include <algorithm>
#include <array>
#include <map>
#include <set>

namespace espocket {
namespace {
constexpr std::array<std::string_view, 4> FIXED = {
    "espocket.app.hello", "espocket.app.hello_runtime",
    "brookesia.general.settings", "brookesia.general.app_store"};
bool eligible(const LauncherApp &app, bool developer)
{
    return app.runtime_id != 0 && !app.manifest_id.empty() && app.runtime && app.visible && app.admitted &&
        (!app.requires_developer || developer) && std::ranges::find(FIXED, app.manifest_id) == FIXED.end();
}
} // namespace

std::string launcher_instance_id(std::string_view manifest)
{
    // Stable FNV-1a 64-bit digest; projection explicitly rejects collisions.
    uint64_t hash = 14695981039346656037ULL;
    for (unsigned char byte : manifest) { hash ^= byte; hash *= 1099511628211ULL; }
    std::string id = "app_";
    constexpr char hex[] = "0123456789abcdef";
    for (int shift = 60; shift >= 0; shift -= 4) id += hex[(hash >> shift) & 15];
    return id;
}

std::expected<std::vector<LauncherEntry>, std::string> project_launcher(
    const std::vector<LauncherApp> &apps, bool developer, LauncherDigest digest)
{
    std::set<std::string> identities;
    std::map<std::string, std::string> instances;
    std::vector<LauncherEntry> entries;
    for (const auto &app : apps) {
        // A duplicate identity anywhere in the full list cannot authorize launch.
        if (!app.manifest_id.empty() && !identities.insert(app.manifest_id).second)
            return std::unexpected("launcher_identity_conflict");
        if (!eligible(app, developer)) continue;
        auto instance = digest(app.manifest_id);
        if (instance.empty() || !instances.emplace(instance, app.manifest_id).second)
            return std::unexpected("launcher_instance_conflict");
        entries.push_back({std::move(instance), app.manifest_id,
                           app.name.empty() ? app.manifest_id : app.name, app.icon});
    }
    std::ranges::sort(entries, [](const auto &a, const auto &b) {
        return a.name == b.name ? a.manifest_id < b.manifest_id : a.name < b.name;
    });
    return entries;
}

std::expected<uint32_t, std::string> resolve_launcher_target(
    const std::vector<LauncherApp> &apps, std::string_view manifest, bool developer)
{
    const LauncherApp *match = nullptr;
    for (const auto &app : apps) {
        if (app.manifest_id != manifest) continue;
        if (match) return std::unexpected("launcher_identity_conflict");
        match = &app;
    }
    if (!match || !eligible(*match, developer)) return std::unexpected("launcher_target_unavailable");
    return match->runtime_id;
}
} // namespace espocket
