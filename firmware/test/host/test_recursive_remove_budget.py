"""The real Core helper waits for a slow recursive deletion and verifies absence."""
from pathlib import Path
import subprocess,tempfile,unittest,sys
ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'firmware/managed_components/espressif__brookesia_system_core'

def run_flow(core):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);(p/'brookesia/service_helper/system').mkdir(parents=True);(p/'private').mkdir()
        (p/'private/utils.hpp').write_text('#pragma once\n#define BROOKESIA_LOGW(...) ((void)0)\n#define BROOKESIA_LOGI(...) ((void)0)\n')
        (p/'brookesia/service_helper/system/storage.hpp').write_text(r'''
#pragma once
#include <expected>
#include <string>
#include <cstdint>
namespace esp_brookesia::service::helper {
struct Storage {
 struct Info {bool exists;};
 static inline bool exists=true,leave_directory=false;
 static inline unsigned duration=6000,remove_budget=0;
 static std::expected<Info,std::string> fs_stat(std::string,uint32_t budget){if(budget!=5000)return std::unexpected("stat budget changed");return Info{exists};}
 static std::expected<void,std::string> fs_remove(std::string,uint32_t budget){remove_budget=budget;if(duration>budget)return std::unexpected("timeout");if(!leave_directory)exists=false;return {};}
};}
''')
        (p/'test.cpp').write_text('#include "'+str(core/'src/private/filesystem.hpp')+'"\n'+r'''
#include <cassert>
int main(){using namespace esp_brookesia;using service::helper::Storage;
 auto result=system::core::remove_path_tree("/apps/sample","runtime app directory");assert(result && *result==1);
 assert(Storage::remove_budget>6000 && Storage::remove_budget<=30000);
 Storage::exists=true;Storage::duration=31000;assert(!system::core::remove_path_tree("/apps/sample","directory"));
 Storage::duration=10;Storage::leave_directory=true;assert(!system::core::remove_path_tree("/apps/sample","directory"));
 assert(!system::core::remove_path_tree("","directory"));
}
''')
        subprocess.run(['c++','-std=c++23','-I',str(p),str(p/'test.cpp'),'-o',str(p/'test')],check=True,capture_output=True)
        return subprocess.run([str(p/'test')],capture_output=True)
class RecursiveRemoveBudgetTest(unittest.TestCase):
    def test_original_budget_rejects_slow_backend(self):self.assertNotEqual(run_flow(SOURCE).returncode,0)
    def test_candidate_waits_and_checks_absence(self):
        sys.path.insert(0,str(ROOT/'scripts/firmware'));from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory() as d:
            core=prepare(SOURCE,ROOT/'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json',Path(d)/'core')
            r=run_flow(core);self.assertEqual(r.returncode,0,r.stderr.decode())
if __name__=='__main__':unittest.main()
