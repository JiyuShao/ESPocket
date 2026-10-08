"""Compile the real projection and real Core snapshot admission method."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1]

class ForegroundRestorationTest(unittest.TestCase):
    def test_stale_instances_core_state_and_consumed_targets(self):
        source = (COMPONENT / 'src/system_lifecycle.cpp').read_text()
        actual = source[source.index('std::optional<RunningInstanceIdentity> System::current_foreground_instance()'):source.index('void System::clear_foreground(')]
        harness = r'''
#include "espocket/foreground_restoration.hpp"
#include <atomic>
#include <cassert>
#include <memory>
namespace esp_brookesia::system::core {enum class AppState {Starting,Running,Stopped,Error};}
namespace espocket {
enum class ShellSurface : uint8_t {Home,Launcher};
using AppState = esp_brookesia::system::core::AppState;
struct App {uint32_t app_id=2; struct {bool visible=true;} manifest;AppState state=AppState::Running;};
struct System {
 uint32_t shell_id_=1;std::atomic<uint32_t> foreground_app_id_=2;
 std::shared_ptr<std::atomic<uint64_t>> foreground_token_=std::make_shared<std::atomic<uint64_t>>(10);
 std::optional<App> active=App{};auto get_active_app()const{return active;}
 std::optional<RunningInstanceIdentity> current_foreground_instance()const;
};
''' + actual + r'''
}
int main(){using namespace espocket;System s;ForegroundRestorationProjection p(ShellSurface::Home);
 auto first=s.current_foreground_instance();assert(first && first->generation==10);
 p.quick_settings_opened({8,1,"canvas"},first);
 assert(p.quick_settings_closed(first,true)->source_id==8);
 assert(!p.quick_settings_closed(first,true));
 p.screen_off(first);p.quick_settings_opened({8,1,"canvas"},first);
 ++*s.foreground_token_;auto second=s.current_foreground_instance();
 assert(p.wake_requires_home(second));assert(!p.quick_settings_closed(second,true));
 for(auto state:{AppState::Starting,AppState::Stopped,AppState::Error}){
   s.active->state=state;assert(!s.current_foreground_instance());
 }
 s.active->state=AppState::Running;s.active->manifest.visible=false;assert(!s.current_foreground_instance());
 s.active->manifest.visible=true;s.foreground_app_id_=3;assert(!s.current_foreground_instance());
 s.foreground_app_id_=2;*s.foreground_token_=0;assert(!s.current_foreground_instance());
 *s.foreground_token_=11;s.active->app_id=1;assert(!s.current_foreground_instance());
 s.active.reset();assert(!s.current_foreground_instance());
 p.quick_settings_opened({8,1,"canvas"},first);assert(!p.quick_settings_closed(std::nullopt,true));
 p.quick_settings_opened({8,1,"stale canvas"},std::nullopt);assert(!p.quick_settings_closed(std::nullopt,true));
 p.quick_settings_opened({1,1,"shell"},std::nullopt);assert(p.quick_settings_closed(std::nullopt,true));
 p.launch_requested(2,ShellSurface::Launcher);assert(p.lifecycle_return(3)==ShellSurface::Home);
 assert(p.lifecycle_return(2)==ShellSurface::Launcher);assert(p.lifecycle_return(2)==ShellSurface::Home);
 p.quick_settings_opened({8,1,"canvas"},first);p.home_requested(2);assert(!p.quick_settings_closed(first,true));
 p.screen_off(first);assert(!p.wake_requires_home(first));assert(!p.sleeping_instance());
 p.launch_requested(2,ShellSurface::Launcher);p.instance_started(3);assert(p.lifecycle_return(2)==ShellSurface::Launcher);
 p.launch_requested(2,ShellSurface::Launcher);p.instance_started(2);assert(p.lifecycle_return(2)==ShellSurface::Home);
 p.screen_off(first);p.quick_settings_opened({8,1,"canvas"},first);p.reset();
 assert(!p.sleeping_instance() && !p.quick_settings_closed(first,true));
}
'''
        with tempfile.TemporaryDirectory() as directory:
            cpp=Path(directory)/'test.cpp'; binary=Path(directory)/'test'; cpp.write_text(harness)
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23','-I',str(COMPONENT/'include'),str(cpp),'-o',str(binary)],check=True)
            subprocess.run([str(binary)],check=True,timeout=10)
