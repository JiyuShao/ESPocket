"""GUI post rejection must fail stop even after successful business on_stop."""
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/firmware'))
from prepare_patched_component import prepare

class CoreGuiCleanupResultTest(unittest.TestCase):
    def exercise(self, core):
        text=(core/'src/app/manager.cpp').read_text()
        start=text.index('    if (!cleanup_result)',text.index('System::stop_app(AppId app_id)'))
        end=text.index('    record.info.state = AppState::Stopped;',start)
        body=text[start:end]
        harness=r'''
#include <cassert>
#include <expected>
#include <string>
#define BROOKESIA_LOGW(...) ((void)0)
constexpr int INVALID_APP_ID=0;constexpr auto LIFECYCLE_ON_STOP="on_stop";
enum class AppState{Stopping,Stopped,Error};
struct Record {struct Info{AppState state=AppState::Stopping;std::string last_error;}info;};
struct Impl {int active_app_id_=7;};
void show_lifecycle_error_dialog(auto&&...){}
struct System {
Impl backing;Impl* impl_=&backing;int failed=0;
void on_app_stop_failed(auto&,auto){++failed;}
std::expected<void,std::string> exercise(bool business_failure,bool post_failure){
Record record;int app_id=7;
std::expected<void,std::string> cleanup_result=post_failure?std::unexpected("GUI rejected"):std::expected<void,std::string>{};
std::expected<void,std::string> stop_result=business_failure?std::unexpected("business failed"):std::expected<void,std::string>{};
''' + body + r'''
return {};}
};
int main(){for(bool business:{false,true})for(bool post:{false,true}){System s;auto result=s.exercise(business,post);assert(bool(result)==(!business && !post));assert(s.failed==int(business || post));if(!result){assert(s.backing.active_app_id_==INVALID_APP_ID);if(post)assert(result.error().find("GUI rejected")!=std::string::npos);if(business)assert(result.error().find("business failed")!=std::string::npos);}}}
'''
        with tempfile.TemporaryDirectory(prefix='core-gui-result-') as directory:
            cpp=Path(directory)/'test.cpp';binary=Path(directory)/'test';cpp.write_text(harness)
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23',str(cpp),'-o',str(binary)],check=True)
            return subprocess.run([str(binary)],text=True,capture_output=True,timeout=10)
    def test_rejected_cleanup_cannot_report_stopped(self):
        core=ROOT/'firmware/managed_components/espressif__brookesia_system_core'
        with tempfile.TemporaryDirectory(prefix='core-gui-copy-') as directory:
            patched=prepare(core,ROOT/'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json',Path(directory)/'core')
            self.assertNotEqual(self.exercise(core).returncode,0)
            result=self.exercise(patched);self.assertEqual(result.returncode,0,result.stderr)
