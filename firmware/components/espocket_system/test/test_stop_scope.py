"""Execute the real System stop hook against foreground/background identities."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[4]
class StopScopeTest(unittest.TestCase):
    def test_all_instances_stop_after_external_entry_revocation_shell_last(self):
        text=(ROOT/'firmware/components/espocket_system/src/system.cpp').read_text()
        body=text[text.index('void System::on_stop()'):text.index('void System::on_deinit()')]
        harness=r'''
#include <atomic>
#include <cassert>
#include <expected>
#include <memory>
#include <string>
#include <vector>
#define ESP_LOGE(...) ((void)0)
#define ESP_LOGW(...) ((void)0)
namespace esp_brookesia::system::core {constexpr int INVALID_APP_ID=0;enum class AppState{Installed,Running,Paused,Stopped,Error};struct AppInfo{int app_id;AppState state;struct{std::string id;}manifest;};}
namespace espocket {
struct Entry {bool closed=false;void close(){closed=true;}void stop(){closed=true;}void cancel_pending(){closed=true;}std::expected<void,std::string> cancel(){closed=true;return {};}};
struct System {
std::atomic_bool stopping_=false;std::atomic<int> foreground_app_id_=2;
std::shared_ptr<std::atomic<int>> foreground_token_=std::make_shared<std::atomic<int>>(22);
std::shared_ptr<Entry> test_snapshots_=std::make_shared<Entry>(),card_actions_=std::make_shared<Entry>(),test_adapter_=std::make_shared<Entry>(),power_key_monitor_=std::make_shared<Entry>(),test_touch_input_=std::make_shared<Entry>(),test_power_input_=std::make_shared<Entry>();
bool navigation_closed=false,card_paused=false,lifecycle_restore_pending_=true;int shell_id_=1,resume_app_id_=2;
std::vector<int> stopped;
void stop_runtime_navigation(){navigation_closed=true;}void pause_card(){card_paused=true;}
auto list_apps(){using namespace esp_brookesia::system::core;return std::vector<AppInfo>{{1,AppState::Running,{"shell"}},{2,AppState::Running,{"native"}},{3,AppState::Paused,{"background"}},{4,AppState::Running,{"runtime"}},{5,AppState::Installed,{"installed"}},{6,AppState::Stopped,{"stopped"}},{7,AppState::Error,{"failed"}}};}
std::expected<void,std::string> stop_app(int id){assert(stopping_ && navigation_closed && card_paused && test_adapter_->closed && power_key_monitor_->closed && test_snapshots_->closed && card_actions_->closed && test_touch_input_->closed && test_power_input_->closed);assert(*foreground_token_==0);stopped.push_back(id);if(id==3)return std::unexpected("business failed");return {};}
void on_stop();
};
''' + body + r'''
}
int main(){espocket::System s;s.on_stop();assert((s.stopped==std::vector<int>{2,3,4,7,1}));assert(s.foreground_app_id_==0 && s.resume_app_id_==0 && !s.lifecycle_restore_pending_);}
'''
        with tempfile.TemporaryDirectory(prefix='system-stop-scope-') as directory:
            cpp=Path(directory)/'test.cpp';binary=Path(directory)/'test';cpp.write_text(harness)
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23',str(cpp),'-o',str(binary)],check=True)
            subprocess.run([str(binary)],check=True,timeout=10)
