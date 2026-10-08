"""Real PWR handler cancels a pending start and the prior visible foreground."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[4]


class StartingPowerHomeTest(unittest.TestCase):
    def test_home_cannot_leave_previous_foreground_or_revive_start(self):
        text=(ROOT/'firmware/components/espocket_system/src/system_power.cpp').read_text()
        actual=text[text.index('void System::handle_power_short_press()'):]
        actual=actual[:actual.rindex('} // namespace espocket')]
        harness=r'''
#include <algorithm>
#include <atomic>
#include "espocket/foreground_restoration.hpp"
#include <cassert>
#include <expected>
#include <memory>
#include <optional>
#include <string>
#include <vector>
#define ESP_LOGW(...) ((void)0)
#define ESP_LOGI(...) ((void)0)
#define CONFIG_ESPOCKET_M6_RESOURCE_TRACE 0
namespace esp_brookesia::system::core {constexpr int INVALID_APP_ID=0;enum class AppState{Starting,Running,Stopping,Stopped};}
namespace espocket {
using AppState=esp_brookesia::system::core::AppState;
enum class ShellSurface : uint8_t {WatchFace,Launcher};
struct App {int app_id;struct{bool visible=true;}manifest;AppState state=AppState::Running;};
struct Shell {int hidden=0;bool watch=false;void discard_overlay_choices(){}void hide_loading(int id,bool){hidden=id;}bool is_watch_face(){return watch;}};
struct System {
 std::atomic_bool stopping_=false,display_on_=true;std::shared_ptr<Shell> shell_=std::make_shared<Shell>();
 int shell_id_=1,homes=0,display_calls=0;
 ForegroundRestorationProjection foreground_restoration_{ShellSurface::WatchFace};
 std::optional<RunningInstanceIdentity> current_foreground_instance(){return std::nullopt;}
 std::vector<App> apps{{2,{},AppState::Starting}};std::optional<App> active;
 std::vector<int> stops;
 auto list_apps(){return apps;}auto get_active_app(){return active;}auto get_app(int){return active;}
 std::expected<void,std::string> stop_app(int id){stops.push_back(id);if(id==2)apps[0].state=AppState::Stopping;else active.reset();return {};}
 std::expected<void,std::string> set_display_on(bool value){++display_calls;display_on_=value;return {};}
 void show_watch_face(){++homes;shell_->watch=true;}
 void handle_power_short_press();
};
''' + actual + r'''
}
int main(){using namespace espocket;
 System loading;loading.handle_power_short_press();assert((loading.stops==std::vector<int>{2}));
 assert(loading.homes==1 && loading.shell_->hidden==2 && loading.foreground_restoration_.lifecycle_return(2)==ShellSurface::WatchFace && loading.display_calls==0);
 System previous;previous.active=App{3,{},AppState::Running};previous.handle_power_short_press();
 assert((previous.stops==std::vector<int>{2,3}) && !previous.active && previous.homes==1);
 System sleeping;sleeping.display_on_=false;sleeping.handle_power_short_press();assert(sleeping.display_on_ && sleeping.stops.empty());
}
'''
        with tempfile.TemporaryDirectory(prefix='espocket-start-power-') as directory:
            root=Path(directory);(root/'test.cpp').write_text(harness)
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23','-I',str(ROOT/'firmware/components/espocket_system/include'),str(root/'test.cpp'),'-o',str(root/'test')],check=True)
            subprocess.run([str(root/'test')],check=True,timeout=10)


if __name__=='__main__':unittest.main()
