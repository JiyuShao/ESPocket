#include "espocket/launcher_projection.hpp"
#include <algorithm>
#include <cstdlib>
#include <iostream>

using namespace espocket;
void require(bool pass, const char *message) { if (!pass) { std::cerr << message << '\n'; std::exit(1); } }
int main()
{
    std::vector<LauncherApp> apps = {
        {7, "org.b", "Same", "", true, true, true, false},
        {8, "org.a", "Same", "icon", true, true, true, false},
        {9, "org.developer", "Dev", "", true, true, true, true},
        {10, "org.hidden", "Hidden", "", true, false, true, false},
        {11, "org.native", "Native", "", false, true, true, false},
        {12, "org.untrusted", "Untrusted", "", true, true, false, false},
        {13, "espocket.app.hello_runtime", "Fixed", "", true, true, true, false},
        {14, "org.fallback", "", "", true, true, true, false},
    };
    auto projected = project_launcher(apps, false);
    require(projected && projected->size() == 3, "filter hidden/native/fixed/untrusted/developer");
    require((*projected)[0].manifest_id == "org.a" && (*projected)[1].manifest_id == "org.b", "name tie has stable identity order");
    require((*projected)[2].name == "org.fallback" && (*projected)[2].icon.empty(), "text and icon fallback");
    auto enabled = project_launcher(apps, true);
    require(enabled && enabled->size() == 4 && (*enabled)[0].manifest_id == "org.developer", "developer admission controls exposure");
    require(!resolve_launcher_target(apps, "org.developer", false), "mode off rejects stale developer click");
    require(*resolve_launcher_target(apps, "org.a", true) == 8, "resolve current runtime identity");
    const auto stable = (*projected)[0].instance;
    apps[1].runtime_id = 88;
    apps[1].name = "Updated";
    require(*resolve_launcher_target(apps, "org.a", true) == 88, "update click resolves new AppId");
    auto updated = project_launcher(apps, false);
    auto found = std::ranges::find_if(*updated, [](const auto &e) { return e.manifest_id == "org.a"; });
    require(found->instance == stable && found->name == "Updated", "metadata update keeps instance identity");
    apps.erase(apps.begin()+1);
    require(!resolve_launcher_target(apps, "org.a", true), "uninstall race rejected");
    require(project_launcher(apps, true) == project_launcher(apps, true), "reboot or repeated notifications rebuild same projection");
    apps.push_back(apps.front());
    require(!project_launcher(apps, true) && !resolve_launcher_target(apps, "org.b", true), "duplicate Core identity rejected");
    apps.pop_back();
    require(!project_launcher(apps, true, [](auto) { return "collision"; }), "instance digest collision rejected");
    require(launcher_instance_id("org.a") == stable && stable != launcher_instance_id("org.b"), "stable digest");
    std::cout << "PASS: Launcher admission, deterministic identity, update/uninstall races and rebuild\n";
}
