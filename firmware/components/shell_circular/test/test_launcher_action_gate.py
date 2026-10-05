"""Compile the real fixed Launcher dispatch against queued actions after launch."""
from pathlib import Path
import os
import re
import subprocess
import tempfile
import unittest

OWNER = Path(__file__).resolve().parents[1]


class LauncherActionGate(unittest.TestCase):
    def test_queued_fixed_actions_do_not_start_a_second_foreground(self):
        source = (OWNER / 'src/circular_shell.cpp').read_text()
        method = source[source.index('std::expected<void, std::string> CircularShell::on_action('):
                        source.index('std::expected<void, std::string> CircularShell::on_timer(')]
        constants = sorted(set(re.findall(r'\b[A-Z][A-Z_]+\b', method)) - {'Launcher'})
        prefix = r'''
#include <atomic>
#include <expected>
#include <functional>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>
namespace esp_brookesia::system::core { struct AppContext {}; }
namespace espocket {
enum class ShellSurface { WatchFace, Launcher };
struct Gesture { std::atomic<int> launcher_pull_distance{0}, launcher_return_threshold{100}; std::atomic<bool> modal_active{false}; };
struct Host { std::function<bool()> app_visible; struct { std::function<bool()> enabled; std::function<std::expected<void,std::string>(bool)> set_enabled; } developer_mode; };
class CircularShell {
public:
 Host host_; ShellSurface surface=ShellSurface::Launcher;
 std::unique_ptr<Gesture> home_gesture_state_=std::make_unique<Gesture>();
 std::vector<std::string> opened; bool visible=false;
 ShellSurface current_surface() { return surface; }
 std::expected<void,std::string> on_action(esp_brookesia::system::core::AppContext &, std::string_view);
 std::expected<void,std::string> open_app(std::string_view id,std::string_view) { opened.emplace_back(id); visible=true; return {}; }
 std::expected<void,std::string> step_brightness() { return {}; }
 std::expected<void,std::string> toggle_wifi() { return {}; }
 void set_status_text(std::string_view,std::string_view) {}
 void refresh_developer_mode() {}
};
'''
        definitions = '\n'.join(f'constexpr std::string_view {name}="{name}";' for name in constants)
        main = r'''
}
int main() {
 using namespace espocket; CircularShell shell; esp_brookesia::system::core::AppContext context;
 shell.host_.app_visible=[&]{return shell.visible;};
 shell.on_action(context, OPEN_APP_STORE_ACTION);
 for (const auto action : {OPEN_HELLO_NATIVE_ACTION, OPEN_HELLO_RUNTIME_ACTION, OPEN_SETTINGS_ACTION, OPEN_APP_STORE_ACTION}) shell.on_action(context, action);
 if (shell.opened.size()!=1) throw std::runtime_error("queued fixed action started another App over Store");
 shell.visible=false;
 shell.on_action(context, OPEN_APP_STORE_ACTION);
 if (shell.opened.size()!=2) throw std::runtime_error("Store could not reopen after Home");
 shell.visible=false; shell.surface=ShellSurface::WatchFace;
 shell.on_action(context, OPEN_APP_STORE_ACTION);
 if (shell.opened.size()!=2) throw std::runtime_error("retired Launcher action started App");
 shell.surface=ShellSurface::Launcher; shell.home_gesture_state_->modal_active=true;
 shell.on_action(context, OPEN_APP_STORE_ACTION);
 if (shell.opened.size()!=2) throw std::runtime_error("modal allowed underlying Launcher action");
}
'''
        with tempfile.TemporaryDirectory(prefix='espocket-launcher-gate-') as temporary:
            directory = Path(temporary)
            (directory / 'main.cpp').write_text(prefix + definitions + '\n' + method + main)
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(directory / 'main.cpp'),
                            '-o', str(directory / 'test')], check=True)
            subprocess.run([str(directory / 'test')], check=True)


if __name__ == '__main__':
    unittest.main()
