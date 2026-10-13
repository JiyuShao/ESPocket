"""Exercise real source selection and System return routing across identity races."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]


class QuickSettingsDisplayTest(unittest.TestCase):
    def test_atomic_owner_checks_and_running_instance_return(self):
        sys.path.insert(0, str(ROOT / 'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='quick-display-') as directory:
            temp = Path(directory)
            selected = prepare(ROOT / 'firmware/managed_components/espressif__brookesia_service_display',
                               ROOT / 'firmware/patches/espressif__brookesia_service_display/0.8.2/manifest.json',
                               temp / 'patched')
            source = (selected / 'src/display_output_source.cpp').read_text()
            method = source[source.index('std::expected<void, std::string> Display::set_active_source('):
                            source.index('std::expected<std::string, std::string> Display::get_active_source(')]
            source = (ROOT / 'firmware/components/espocket_system/src/system_display.cpp').read_text()
            system = source[source.index('std::expected<void, std::string> System::set_quick_settings_display('):
                            source.index('void System::report_startup_failure')]
            harness = r'''
#include <algorithm>
#include <atomic>
#include "espocket/foreground_restoration.hpp"
#include <cassert>
#include <expected>
#include <functional>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <set>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS()
#define ESP_LOGW(...) ((void)0)
namespace esp_brookesia::service {
constexpr uint32_t INVALID_SOURCE_ID=0;
struct AsyncFrame {uint32_t source_id;};
enum class SourceState {Dummy,Granted};enum class PresentResult {DroppedNotActive};
struct SourceInfo {uint32_t id;std::string name;};
struct Source {SourceInfo info;std::set<std::string> requested_outputs;};
struct Output {struct {std::string name="panel";} info;uint32_t active_source_id=2;std::optional<AsyncFrame> pending_frame;};
struct Display {
 std::mutex mutex_;std::map<uint32_t,Output> outputs_{{1,{}}};
 std::map<uint32_t,Source> sources_{{1,{{1,"LVGL"},{}}},{2,{{2,"game"},{}}}};
 int events=0,completed=0;std::function<void()> snapshot_race;
 struct SourceSelectionGuard {uint32_t current_id;uint32_t next_id;};
 static Display& get_instance(){static Display value;return value;}
 std::expected<uint32_t,std::string> find_output_id_locked(std::string_view name){if(name!="panel")return std::unexpected("output");return 1;}
 std::expected<uint32_t,std::string> find_source_id_locked(std::string_view name){for(auto& [id,s]:sources_)if(s.info.name==name)return id;return std::unexpected("source");}
 std::expected<void,std::string> set_active_source(std::string_view,std::string_view,std::optional<SourceSelectionGuard> guard=std::nullopt);
 void emit_source_state_changed(auto,auto,auto){++events;}void emit_active_source_changed(auto,auto){++events;}
 void complete_async_frame(AsyncFrame,PresentResult){++completed;}
 std::expected<std::string,std::string> get_active_source(std::string_view){auto i=sources_.find(outputs_[1].active_source_id);if(i==sources_.end())return std::unexpected("invalid");return i->second.info.name;}
 std::vector<SourceInfo> get_sources(){std::vector<SourceInfo> result;for(auto& [id,s]:sources_)result.push_back(s.info);if(snapshot_race){auto callback=std::exchange(snapshot_race,{});callback();}return result;}
};
''' + method + r'''
}
namespace esp_brookesia::gui::lvgl {constexpr std::string_view DISPLAY_SOURCE_NAME="LVGL";}
namespace espocket {
struct DisplaySource {static DisplaySource& get_instance(){static DisplaySource value;return value;}
 std::string output_name(){return "panel";}uint32_t source_id(){return 1;}};
enum class ShellSurface : uint8_t {WatchFace};
struct System {
 std::atomic_bool stopping_=false;bool quick_settings_cover_=false,fail_pause=false;
 struct Execution {uint64_t instance;};
 std::vector<std::pair<bool,bool>> reasons;
 auto app_execution_state(uint32_t)->std::optional<Execution>{return Execution{foreground_token_->load()};}
 std::expected<void,std::string>set_app_suspension(uint32_t,uint64_t,bool cover,bool off){reasons.push_back({cover,off});if(fail_pause)return std::unexpected("failed");return {};}
 void sync_foreground_suspension();
 std::atomic_bool display_on_=true;std::shared_ptr<std::atomic<uint64_t>> foreground_token_=std::make_shared<std::atomic<uint64_t>>(7);
 ForegroundRestorationProjection foreground_restoration_{ShellSurface::WatchFace};
 std::optional<RunningInstanceIdentity> current_foreground_instance(){return RunningInstanceIdentity{2,foreground_token_->load()};}
 std::expected<void,std::string> set_quick_settings_display(bool,bool);
};
''' + system + r'''
}
int main(){using namespace esp_brookesia::service;auto& d=Display::get_instance();espocket::System system;
 using Guard=Display::SourceSelectionGuard;
 d.outputs_[1].pending_frame=AsyncFrame{2};
 assert(!d.set_active_source("panel","LVGL",Guard{9,1}));
 assert(!d.set_active_source("panel","LVGL",Guard{2,9}));
 assert(d.events==0 && d.outputs_[1].active_source_id==2 && d.outputs_[1].pending_frame);
 assert(d.sources_[1].requested_outputs.empty());
 assert(system.set_quick_settings_display(true,false));
 assert(d.outputs_[1].active_source_id==1 && d.completed==1);
 assert((system.reasons.back()==std::pair{true,false}));
 system.display_on_=false;system.sync_foreground_suspension();assert((system.reasons.back()==std::pair{true,true}));
 system.display_on_=true;system.sync_foreground_suspension();assert((system.reasons.back()==std::pair{true,false}));
 assert(system.set_quick_settings_display(false,true));assert(d.outputs_[1].active_source_id==2);
 assert((system.reasons.back()==std::pair{false,false}));
 // Lifecycle failure does not trap Quick Settings or source routing.
 system.fail_pause=true;assert(system.set_quick_settings_display(true,false));
 assert(system.set_quick_settings_display(false,true));system.fail_pause=false;
 assert(system.set_quick_settings_display(true,false));++*system.foreground_token_;
 assert(system.set_quick_settings_display(false,true));assert(d.outputs_[1].active_source_id==1);
 d.outputs_[1].active_source_id=2;assert(system.set_quick_settings_display(true,false));
 assert(system.set_quick_settings_display(false,false));assert(d.outputs_[1].active_source_id==1);
 d.outputs_[1].active_source_id=2;assert(system.set_quick_settings_display(true,false));
 d.sources_.erase(2);d.sources_[3]={{3,"game"},{}};
 assert(system.set_quick_settings_display(false,true));assert(d.outputs_[1].active_source_id==1);
 // Replace the original registration after System reads its source inventory.
 d.sources_.erase(3);d.sources_[2]={{2,"game"},{}};d.outputs_[1].active_source_id=2;
 assert(system.set_quick_settings_display(true,false));
 d.snapshot_race=[&]{d.sources_.erase(2);d.sources_[3]={{3,"game"},{}};};
 assert(!system.set_quick_settings_display(false,true));assert(d.outputs_[1].active_source_id==1);
 // Change active Owner between snapshot and takeover: no output or lease mutation.
 d.outputs_[1].active_source_id=3;d.snapshot_race=[&]{d.outputs_[1].active_source_id=1;};
 assert(!system.set_quick_settings_display(true,false));assert(!system.foreground_restoration_.quick_settings_closed(system.current_foreground_instance(),true));
 system.display_on_=false;assert(!system.set_quick_settings_display(true,false));
}
'''
            cpp = temp / 'test.cpp'; binary = temp / 'test'; cpp.write_text(harness)
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23','-I',str(ROOT/'firmware/components/espocket_system/include'), '-pthread', str(cpp), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=10)


if __name__ == '__main__':
    unittest.main()
