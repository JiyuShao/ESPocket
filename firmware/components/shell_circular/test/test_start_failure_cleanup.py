"""Run the real Native Shell start method with acquisition failures."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[4]

class ShellStartFailureCleanupTest(unittest.TestCase):
    def test_native_start_failure_releases_its_display_and_state(self):
        text=(ROOT/'firmware/components/shell_circular/src/circular_shell.cpp').read_text()
        method=text[text.index('std::expected<void, std::string> CircularShell::on_start('):text.index('std::expected<void, std::string> CircularShell::on_stop(')]
        actions=['OPEN_HELLO_NATIVE_ACTION','OPEN_HELLO_RUNTIME_ACTION','OPEN_SETTINGS_ACTION','OPEN_SETTINGS_CARD_ACTION','OPEN_SETTINGS_QUICK_ACTION','OPEN_APP_STORE_ACTION','OPEN_DYNAMIC_APP_ACTION','STEP_BRIGHTNESS_ACTION','STEP_BRIGHTNESS_QUICK_ACTION','TOGGLE_WIFI_ACTION','TOGGLE_DEVELOPER_MODE_ACTION']
        harness=r'''
#include <atomic>
#include <cassert>
#include <expected>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <string_view>
#include <cstdint>
#include <stdexcept>
#define ESP_LOGI(...) ((void)0)
int fail=0,stage=0;bool inject(){return ++stage==fail;}
int esp_timer_get_time(){return 0;}
struct Connection {bool active=false;void disconnect(){active=false;}};
struct Binding {bool valid=false;void release(){valid=false;}};
struct LvglLock {explicit operator bool() const {return true;}};
struct PointerClickFilters {void remove(){}};
namespace esp_brookesia {
namespace lib_utils {struct FunctionGuard {std::function<void()> fn;FunctionGuard(std::function<void()> f):fn(f){}~FunctionGuard(){if(fn)fn();}void release(){fn={};}};}
namespace gui {struct Event{std::string path;};}
namespace system::core {constexpr int INVALID_TIMER_ID=-1;
struct Gui {std::expected<void,std::string> subscribe_action(auto){if(inject())return std::unexpected("action");return {};}
Connection subscribe_action(auto,auto){return {true};}};
struct Timer {bool active=false;std::expected<int,std::string> start_periodic(auto,auto){if(inject())return std::unexpected("timer");active=true;return 1;}bool stop(int){active=false;return true;}};
struct AppContext {Gui g;Timer t;Gui& gui(){return g;}Timer& timer(){return t;}};
}}
namespace espocket {
''' + '\n'.join(f'constexpr auto {name}="{name}";' for name in actions) + r'''
constexpr auto HOME_INTENT_TIMER="home";constexpr int HOME_INTENT_INTERVAL_MS=20;
struct LoadingState {std::mutex mutex;void* overlay=nullptr;};struct KeyboardState {std::mutex mutex;void* overlay=nullptr;};struct MessageDialogState {std::mutex mutex;void* overlay=nullptr;};struct BackOverlayState {void* button=nullptr;void* card_hint=nullptr;};struct HomeGestureState {};
struct CircularShell {
std::shared_ptr<PointerClickFilters> pointer_click_filters_;
struct CallbackState{std::mutex mutex;CircularShell* owner=nullptr;};
esp_brookesia::system::core::AppContext* context_=nullptr;
std::shared_ptr<LoadingState> loading_state_;std::shared_ptr<KeyboardState> keyboard_state_;std::shared_ptr<MessageDialogState> message_dialog_state_;
std::shared_ptr<BackOverlayState> back_overlay_state_;std::shared_ptr<HomeGestureState> home_gesture_state_;
std::shared_ptr<CallbackState> callback_state_;
Connection gesture_connection_,launcher_connection_;Binding display_binding_;
int last_activity_generation_=0,last_activity_us_=0,home_intent_timer_id_=-1;bool screen_timeout_latched_=false;
uint64_t launcher_generation_=0;int launcher_refresh_at_us_=0;
std::mutex launcher_intent_mutex_;std::string launcher_intent_;
std::expected<void,std::string> load_theme_colors(){if(inject())return std::unexpected("theme");return {};}
std::expected<void,std::string> configure_home_gesture(){display_binding_.valid=true;gesture_connection_.active=true;if(inject())return std::unexpected("gesture");pointer_click_filters_=std::make_shared<PointerClickFilters>();return {};}
void refresh_launcher(){if(inject())throw std::runtime_error("launcher");}void start_status(){}
std::expected<void,std::string> on_start(esp_brookesia::system::core::AppContext&);
};
''' + method + r'''
}
int main(){for(int point=1;point<=14;++point){stage=0;fail=point;espocket::CircularShell shell;esp_brookesia::system::core::AppContext context;
assert(!shell.on_start(context));assert(!shell.display_binding_.valid);assert(!shell.gesture_connection_.active);
assert(!shell.context_);assert(!shell.loading_state_ && !shell.keyboard_state_ && !shell.message_dialog_state_ && !shell.back_overlay_state_ && !shell.home_gesture_state_);assert(!context.t.active);}
stage=0;fail=15;espocket::CircularShell partial;esp_brookesia::system::core::AppContext partial_context;
try{(void)partial.on_start(partial_context);assert(false);}catch(const std::runtime_error&){}
assert(!partial.pointer_click_filters_ && !partial.home_gesture_state_ && !partial.context_);
assert(!partial.gesture_connection_.active && !partial.display_binding_.valid && !partial_context.t.active);
stage=0;fail=0;espocket::CircularShell shell;esp_brookesia::system::core::AppContext context;assert(shell.on_start(context));assert(shell.context_ && shell.display_binding_.valid && context.t.active);}
'''
        with tempfile.TemporaryDirectory(prefix='shell-start-cleanup-') as directory:
            cpp=Path(directory)/'test.cpp';binary=Path(directory)/'test';cpp.write_text(harness)
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23',str(cpp),'-o',str(binary)],check=True)
            subprocess.run([str(binary)],check=True,timeout=10)
