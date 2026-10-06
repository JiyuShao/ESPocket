"""Run fatal diagnostic acquisition, lock, and allocation failure boundaries."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[4]
class StartupDiagnosticTest(unittest.TestCase):
    def test_display_is_retained_only_for_a_successful_fatal_diagnostic(self):
        text=(ROOT/'firmware/components/espocket_system/src/system_display.cpp').read_text()
        method=text[text.index('void System::report_startup_failure('):text.index('void System::stop_display()')]
        harness=r'''
#include <atomic>
#include <cassert>
#include <cstdint>
#include <expected>
#include <string>
#include <string_view>
#define ESP_LOGE(...) ((void)0)
constexpr int ESP_OK=0,LV_TEXT_ALIGN_CENTER=0;
bool lock_ok=true,screen_ok=true,label_ok=true;int locks=0,unlocks=0;std::string message;
int esp_lv_adapter_lock(int timeout){assert(timeout==1000);++locks;return lock_ok?0:1;}
void esp_lv_adapter_unlock(){++unlocks;}
int* lv_screen_active(){static int screen;return screen_ok?&screen:nullptr;}
void lv_obj_clean(int*){}int lv_color_hex(int x){return x;}void lv_obj_set_style_bg_color(auto...){}
int* lv_label_create(int*){static int label;return label_ok?&label:nullptr;}
void lv_obj_set_width(int*,int32_t width){assert(width==349);}void lv_obj_set_style_text_align(auto...){}
void lv_obj_set_style_text_color(auto...){}void lv_obj_center(int*){}
void lv_label_set_text(int*,const char* text){message=text;}
namespace espocket {struct System {bool startup_failed_=false,display_started_=false,display_ok=true;std::atomic_bool stopping_=false;int starts=0,stops=0;unsigned display_width_=466;
std::expected<void,std::string> start_display(){++starts;if(!display_ok)return std::unexpected("display");display_started_=true;return {};}
void stop_display(){assert(display_started_);display_started_=false;++stops;}
void report_startup_failure(std::string_view);};
''' + method + r'''
}
int main(){for(bool existing:{false,true})for(int failure=0;failure<=4;++failure){if(existing && failure==1)continue;
locks=unlocks=0;message.clear();lock_ok=failure!=2;screen_ok=failure!=3;label_ok=failure!=4;
espocket::System s;s.display_started_=existing;s.display_ok=failure!=1;s.report_startup_failure("private diagnostic");
assert(s.startup_failed_ && s.stopping_);assert(s.starts==int(!existing));assert(s.display_started_==(failure==0));assert(s.stops==int(failure>1));assert(unlocks==int(failure!=1 && failure!=2));
if(failure==0)assert(message=="Startup failed\nRestart device");}}
'''
        with tempfile.TemporaryDirectory(prefix='startup-diagnostic-') as directory:
            cpp=Path(directory)/'test.cpp';binary=Path(directory)/'test';cpp.write_text(harness)
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23',str(cpp),'-o',str(binary)],check=True)
            subprocess.run([str(binary)],check=True,timeout=10)
