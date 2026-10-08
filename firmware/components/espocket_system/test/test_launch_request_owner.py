"""Exercise real product acceptance bookkeeping; Core owns pending startup."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[4]


class LaunchRequestOwnerTest(unittest.TestCase):
    def test_rejected_and_repeated_requests_preserve_original_owner(self):
        text=(ROOT/'firmware/components/espocket_system/src/system_navigation.cpp').read_text()
        actual=text[text.index('std::expected<void, std::string> System::launch_app('):text.index('void System::handle_back(')]
        harness=r'''
#include <algorithm>
#include "espocket/foreground_restoration.hpp"
#include <cassert>
#include <expected>
#include <memory>
#include <string>
#include <string_view>
#include <vector>
#define ESP_LOGW(...) ((void)0)
namespace esp_brookesia::system::core {enum class AppState{Installed,Starting,Running,Stopping};}
namespace espocket {
using AppState=esp_brookesia::system::core::AppState;
enum class ShellSurface : uint8_t {WatchFace,Launcher,QuickSettings};
struct App {int app_id;struct {std::string id;bool visible=true;}manifest;AppState state=AppState::Installed;};
struct Shell {int loading_owner=0,loading_calls=0;std::expected<void,std::string> show_loading(int id,bool){loading_owner=id;++loading_calls;return {};}};
struct System {
 std::vector<App> apps{{1,{"first"}},{2,{"second"}}};std::shared_ptr<Shell> shell_=std::make_shared<Shell>();
 ForegroundRestorationProjection foreground_restoration_{ShellSurface::WatchFace};
 int owner=0,requests=0;
 auto list_apps(){return apps;}
 std::expected<void,std::string> request_app_start(int id){++requests;if(owner)return std::unexpected("busy");owner=id;apps[id-1].state=AppState::Starting;return {};}
 std::expected<void,std::string> launch_app(std::string_view,ShellSurface);
};
''' + actual + r'''
}
int main(){using namespace espocket;System s;assert(s.launch_app("first",ShellSurface::Launcher));
 assert(s.owner==1 && s.shell_->loading_owner==1 && s.foreground_restoration_.lifecycle_return(99)==ShellSurface::WatchFace);
 assert(!s.launch_app("second",ShellSurface::QuickSettings));
 assert(s.owner==1 && s.shell_->loading_owner==1 && s.shell_->loading_calls==1);
 assert(s.foreground_restoration_.lifecycle_return(1)==ShellSurface::Launcher);
 assert(s.launch_app("first",ShellSurface::QuickSettings));assert(s.requests==2 && s.shell_->loading_calls==1);
 s.apps[0].state=AppState::Running;assert(s.launch_app("first",ShellSurface::WatchFace));assert(s.shell_->loading_calls==1);
 assert(!s.launch_app("missing",ShellSurface::WatchFace));
}
'''
        with tempfile.TemporaryDirectory(prefix='espocket-launch-owner-') as directory:
            root=Path(directory);(root/'test.cpp').write_text(harness)
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23','-I',str(ROOT/'firmware/components/espocket_system/include'),str(root/'test.cpp'),'-o',str(root/'test')],check=True)
            subprocess.run([str(root/'test')],check=True,timeout=10)


if __name__=='__main__':unittest.main()
