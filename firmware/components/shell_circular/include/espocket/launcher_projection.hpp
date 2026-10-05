#pragma once

#include <cstdint>
#include <expected>
#include <functional>
#include <string>
#include <string_view>
#include <vector>

namespace espocket {

// Supplied by System from the committed Core list and Core admission results.
struct LauncherApp {
    uint32_t runtime_id = 0;
    std::string manifest_id;
    std::string name;
    std::string icon;
    bool runtime = true;
    bool visible = true;
    bool admitted = false;
    bool requires_developer = false;
};
struct LauncherEntry {
    std::string instance;
    std::string manifest_id;
    std::string name;
    std::string icon;
    bool operator==(const LauncherEntry &) const = default;
};
using LauncherDigest = std::function<std::string(std::string_view)>;
std::string launcher_instance_id(std::string_view manifest);
std::expected<std::vector<LauncherEntry>, std::string> project_launcher(
    const std::vector<LauncherApp> &apps, bool developer_enabled,
    LauncherDigest digest = launcher_instance_id);
std::expected<uint32_t, std::string> resolve_launcher_target(
    const std::vector<LauncherApp> &apps, std::string_view manifest, bool developer_enabled);

} // namespace espocket
