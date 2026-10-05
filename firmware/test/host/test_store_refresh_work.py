"""Remote index Refresh must not compete with a redundant local package scan."""
from pathlib import Path
import subprocess,tempfile,unittest,sys
ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'firmware/managed_components/espressif__brookesia_app_store'

def run_flow(component):
    text=(component/'src/app/lifecycle.ipp').read_text()
    actual=text[text.index('std::expected<void, std::string> AppStoreApp::execute_deferred_refresh('):text.index('std::expected<void, std::string> AppStoreApp::subscribe_actions(')]
    code=r'''
#include <cassert>
#include <expected>
#include <string>
namespace systemx::core {struct AppContext {};}
struct AppStoreApp {
 enum class ViewMode {Store,Local,Installed};ViewMode view_mode_=ViewMode::Store;
 unsigned scans=0,remote=0,installed=0,capacity=0,canceled=0;
 void cancel_startup_load(auto&){}void cancel_local_package_scan(auto&){++canceled;}
 void refresh_installed_apps(auto&){++installed;}void refresh_storage_capacity(auto&){++capacity;}
 void start_local_package_scan(auto&,bool){++scans;}
 std::expected<void,std::string> start_remote_refresh(auto&){++remote;return {};}
 std::expected<void,std::string> populate_entries(auto&){return {};}
 std::string status_text_;
 std::expected<void,std::string> execute_deferred_refresh(systemx::core::AppContext&,ViewMode);
};
'''+actual.replace('system::core','systemx::core')+r'''
int main(){AppStoreApp app;systemx::core::AppContext ctx;
 assert(app.execute_deferred_refresh(ctx,AppStoreApp::ViewMode::Store));
 assert(app.remote==1 && app.scans==0 && app.installed==1 && app.capacity==1);
 app.view_mode_=AppStoreApp::ViewMode::Local;
 assert(app.execute_deferred_refresh(ctx,AppStoreApp::ViewMode::Local));assert(app.scans==1 && app.remote==1);
 app.view_mode_=AppStoreApp::ViewMode::Installed;
 assert(app.execute_deferred_refresh(ctx,AppStoreApp::ViewMode::Installed));assert(app.scans==1 && app.remote==1);
}
'''
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'test.cpp';p.write_text(code);exe=Path(d)/'test'
        subprocess.run(['c++','-std=c++23',str(p),'-o',str(exe)],check=True,capture_output=True)
        return subprocess.run([str(exe)],capture_output=True)

class StoreRefreshWorkTest(unittest.TestCase):
    def test_original_refresh_starts_redundant_scan(self):self.assertNotEqual(run_flow(SOURCE).returncode,0)
    def test_candidate_keeps_local_refresh(self):
        sys.path.insert(0,str(ROOT/'scripts/firmware'));from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory() as d:
            component=prepare(SOURCE,ROOT/'firmware/patches/espressif__brookesia_app_store/0.8.2/manifest.json',Path(d)/'component')
            r=run_flow(component);self.assertEqual(r.returncode,0,r.stderr.decode())
if __name__=='__main__':unittest.main()
