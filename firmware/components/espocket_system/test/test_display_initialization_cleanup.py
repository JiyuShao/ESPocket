"""Inject each Display startup failure into the real product method."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[4]

class DisplayInitializationCleanupTest(unittest.TestCase):
    def test_failed_start_releases_only_acquired_source_and_binding(self):
        text = (ROOT / 'firmware/components/espocket_system/src/system_display.cpp').read_text()
        method = text[text.index('std::expected<void, std::string> System::start_display()'):text.rindex('} // namespace espocket')]
        # Stop before the unrelated Brightness seam: every failing return is above it.
        success = '    cleanup.release();\n' if 'FunctionGuard cleanup' in method else ''
        method = method[:method.index('    // One selected output')] + success + '    return {};\n}\n'
        cleanup = ''
        if 'System::stop_display()' in text:
            cleanup = text[text.index('void System::stop_display()'):text.index('std::expected<void, std::string> System::start_display()')]
        harness = r'''
#include <algorithm>
#include <atomic>
#include <cassert>
#include <expected>
#include <functional>
#include <optional>
#include <string>
#include <vector>
int fail=0, stage=0;
bool injected(){return ++stage==fail;}
namespace boost::json { struct array{};struct value{value(array){}}; }
struct Binding {bool valid=false; int releases=0; bool is_valid(){return valid;} void release(){if(valid){++releases;valid=false;}}};
struct Manager { Binding bind(const char*) {return Binding{!injected()};} static Manager& get_instance(){static Manager m;return m;}};
namespace esp_brookesia {namespace lib_utils {struct FunctionGuard {std::function<void()> fn; FunctionGuard(std::function<void()> f):fn(f){}~FunctionGuard(){if(fn)fn();}void release(){fn={};}};} namespace service {using ServiceManager=Manager;namespace helper {struct Timeout{Timeout(int){}};}}
namespace gui::lvgl {struct DisplaySourceConfig{std::string output_name;unsigned buffer_height=40;};constexpr auto DISPLAY_SOURCE_ROLE="gui";}}
struct DisplayHelper { enum class FunctionId{GetOutputs,SetBacklightOnOff,SetActiveSourceRole};
struct OutputInfo {std::string name="display"; unsigned id=1,width=466,height=466;std::optional<int> touch=1,backlight=1;};
static bool is_available(){return !injected();} static std::string get_name(){return "Display";}
template<class T=void,class... A> static std::expected<T,std::string> call_function_sync(FunctionId,A&&...){if(injected())return std::unexpected("injected");if constexpr(!std::is_void_v<T>)return T{};else return {};}};
bool parse(boost::json::value,std::vector<DisplayHelper::OutputInfo>& out){if(injected())return false;out.push_back({});if(injected())out[0].touch.reset();return true;}
#define BROOKESIA_DESCRIBE_FROM_JSON(v,o) parse(v,o)
struct DisplaySource {bool started=false;int stops=0;static DisplaySource& get_instance(){static DisplaySource s;return s;}bool start(auto config){assert(config.buffer_height*466*2<=24576);if(injected())return false;started=true;return true;}void stop(){assert(started);started=false;++stops;}};
constexpr int DISPLAY_TIMEOUT_MS=10;
namespace espocket {
struct System {Binding display_binding_;bool display_started_=false;unsigned display_width_=0,display_height_=0,display_output_id_=0;
void stop_display();std::expected<void,std::string> start_display();};
''' + cleanup + method + r'''
}
int main(){for(int point=1;point<=8;++point){stage=0;fail=point;espocket::System s;auto& source=DisplaySource::get_instance();source={};auto result=s.start_display();assert(!result);assert(!s.display_binding_.valid);assert(!source.started);assert(!s.display_started_);assert(source.stops==(point==8?1:0));}
stage=0;fail=0;espocket::System s;assert(s.start_display());assert(s.display_binding_.valid && s.display_started_);}
'''
        with tempfile.TemporaryDirectory(prefix='display-cleanup-') as directory:
            cpp=Path(directory)/'test.cpp';binary=Path(directory)/'test';cpp.write_text(harness)
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23',str(cpp),'-o',str(binary)],check=True)
            subprocess.run([str(binary)],check=True,timeout=10)
