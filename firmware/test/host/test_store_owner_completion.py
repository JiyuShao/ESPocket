"""Exercise the real cached-read callback across worker completion and stop."""
from pathlib import Path
import subprocess, tempfile, unittest
ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'firmware/managed_components/espressif__brookesia_app_store'

def run_flow(component):
    text = (component / 'src/network/remote_index.ipp').read_text()
    begin = text.index('void AppStoreApp::submit_next_cached_index_load(')
    end = text.index('void AppStoreApp::handle_cached_index_load_result(', begin)
    actual = text[begin:end]
    header = component / 'src/private/app_store_impl.hpp'
    impl = header.read_text()
    if 'class OwnerCompletion' not in impl:
        # Feed the identical candidate mailbox to the unchanged upstream call site.
        import sys
        sys.path.insert(0,str(ROOT/'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory() as d:
            candidate=prepare(SOURCE,ROOT/'firmware/patches/espressif__brookesia_app_store/0.8.2/manifest.json',Path(d)/'component')
            impl=(candidate/'src/private/app_store_impl.hpp').read_text()
    include = '#include <deque>\n#include <mutex>\nnamespace esp_brookesia::app::app_store {\n' + impl[impl.index('class OwnerCompletion'):impl.index('struct AppStoreApp::Impl')] + '}' 
    harness = r'''
#include <cassert>
#include <cstdint>
#include <filesystem>
#include <functional>
#include <memory>
#include <string>
#include <thread>
#include <vector>
''' + include + r'''
#define BROOKESIA_LOGW(...) ((void)0)
namespace service {using FunctionResult=int; struct ServiceBase {using FunctionResultHandler=std::function<void(int&&)>;};}
struct StorageHelper {enum class FunctionId{FSReadText}; static inline service::ServiceBase::FunctionResultHandler callback;
static bool call_function_async(FunctionId,std::string,service::ServiceBase::FunctionResultHandler h){callback=std::move(h);return true;}};
using namespace esp_brookesia::app::app_store;
struct AppStoreApp {
 void* context_=this;uint64_t async_generation_=1;bool startup_cache_load_in_progress_=true;
 size_t startup_cache_cursor_=0;std::vector<std::filesystem::path> startup_cache_candidates_{"cache/index.json"};std::string startup_cache_last_error_;
 std::shared_ptr<OwnerCompletion> owner_completions_=std::make_shared<OwnerCompletion>();
 int handled=0;std::thread::id owner=std::this_thread::get_id();
 void handle_cached_index_load_result(uint64_t,std::filesystem::path,int&&){assert(std::this_thread::get_id()==owner);++handled;}
 void finish_cached_index_load_without_cache(std::string){}
 void submit_next_cached_index_load(uint64_t);
};
''' + actual + r'''
int main(){
 AppStoreApp app;app.submit_next_cached_index_load(1);
 std::thread worker([]{StorageHelper::callback(7);});worker.join();assert(app.handled==0);
 assert(app.owner_completions_->drain_one());assert(app.handled==1);
 app.startup_cache_cursor_=0;app.submit_next_cached_index_load(1);auto old=StorageHelper::callback;
 old(8);app.owner_completions_->close();assert(!app.owner_completions_->drain_one());
 app.owner_completions_=std::make_shared<OwnerCompletion>();old(9);assert(!app.owner_completions_->drain_one());assert(app.handled==1);
 app.startup_cache_cursor_=0;app.submit_next_cached_index_load(1);StorageHelper::callback(10);
 assert(app.owner_completions_->drain_one());assert(app.handled==2);
}
'''
    with tempfile.TemporaryDirectory(prefix='store-owner-') as directory:
        src=Path(directory)/'test.cpp';src.write_text(harness)
        subprocess.run(['c++','-std=c++20','-pthread','-I',str(header.parent),str(src),'-o',str(Path(directory)/'test')],check=True,capture_output=True)
        return subprocess.run([str(Path(directory)/'test')],capture_output=True)

class StoreOwnerCompletionTest(unittest.TestCase):
    def test_upstream_callback_runs_on_worker(self):
        # The same cached-read call site must be red before the Owner handoff.
        with tempfile.TemporaryDirectory(prefix='store-original-') as directory:
            import shutil
            component=Path(directory)/'component';shutil.copytree(SOURCE,component)
            self.assertNotEqual(run_flow(component).returncode,0)

    def test_patched_callback_handoff_and_stop(self):
        import sys
        sys.path.insert(0,str(ROOT/'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='store-patched-') as directory:
            component=prepare(SOURCE,ROOT/'firmware/patches/espressif__brookesia_app_store/0.8.2/manifest.json',Path(directory)/'component')
            result=run_flow(component)
            self.assertEqual(result.returncode,0,result.stderr.decode())

if __name__=='__main__':unittest.main()
