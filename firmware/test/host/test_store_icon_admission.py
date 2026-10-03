"""Exercise pinned Store icon submission and async capacity rejection, not a copy."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'firmware/managed_components/espressif__brookesia_app_store'


def run_control_flow(component):
    text = (component / 'src/network/http.ipp').read_text()
    start = text.index('std::expected<void, std::string> AppStoreApp::process_refresh_icon_step(')
    end = text.index('void AppStoreApp::schedule_refresh_icon_step(', start)
    actual = text[start:end]
    harness = r'''
#include <cassert>
#include <cstdint>
#include <expected>
#include <filesystem>
#include <functional>
#include <optional>
#include <string>
#include <vector>
#define BROOKESIA_LOGW(...) ((void)0)
#define BROOKESIA_LOGD(...) ((void)0)
namespace test {
namespace system::core {struct AppContext {};}
struct HttpHelper {enum class FunctionId{CancelRequest}; template<class... T> static bool call_function_async(T...) {return true;}};
struct AppStoreApp {
 enum class IconUpdatePurpose {None, LazyVisiblePage}; enum class ViewMode{Remote,Local}; enum class VisibleItemKind{Store,Installed,Local};
 struct VisibleItemRef{VisibleItemKind kind=VisibleItemKind::Store; size_t index=0;};
 struct Entry {std::string package_name="sample",manifest_id="sample",icon_url="https://example.invalid/icon.png",icon_file_path;
 uint64_t icon_request_id=0;std::filesystem::path icon_download_path;};
 struct Installed {struct {struct {std::string id;} manifest;} app;std::string pending_icon_resource_id;};
 struct Request {std::string download_path;size_t max_file_size=0;};
 static constexpr size_t ICON_MAX_FILE_SIZE=4096;
 static constexpr uint32_t SIZE_METADATA_RETRY_DELAY_MS=500;
 system::core::AppContext* context_=nullptr;uint64_t refresh_icon_request_id_=0;
 IconUpdatePurpose refresh_icon_purpose_=IconUpdatePurpose::LazyVisiblePage;ViewMode view_mode_=ViewMode::Remote;
 size_t refresh_icon_cursor_=0;std::vector<VisibleItemRef> refresh_icon_indices_{{}};std::vector<Entry> entries_{{}};
 std::vector<Installed> installed_runtime_apps_;bool http_available_=true;
 unsigned advanced=0,scheduled=0,submitted=0;uint32_t delay=0;
 std::function<void(uint64_t)> success;std::function<void(std::string)> failure;
 void apply_pending_icon_resources(auto&){} void reset_refresh_icon_state(){refresh_icon_purpose_=IconUpdatePurpose::None;}
 void finish_refresh_icon_update(auto&){reset_refresh_icon_state();}
 std::optional<VisibleItemRef> current_refresh_icon_ref(){return refresh_icon_indices_[refresh_icon_cursor_];}
 void advance_refresh_icon_step(auto&){++advanced;++refresh_icon_cursor_;}
 void schedule_refresh_icon_step(auto&,uint32_t value=0){++scheduled;delay=value;}
 std::string register_cached_icon(auto&,std::initializer_list<std::string>){return {};}
 bool should_fetch_icon(const auto&){return true;}
 std::vector<std::filesystem::path> cached_icon_file_candidates(auto&,std::initializer_list<std::string>){return {};}
 bool read_png_size(auto&){return false;}void remove_invalid_icon_file(auto&,const char*){}
 std::expected<void,std::string> register_icon(auto&,size_t){return {};}
 std::optional<std::filesystem::path> writable_cache_file(auto&,const auto&){return "/inert-test-icon";}
 std::string icon_cache_relative_path(const auto&){return "icon";}
 Request make_get_request(const auto&){return {};}
 bool submit_http_request_async(auto&,Request,std::function<void(uint64_t)> ok,std::function<void(std::string)> fail){
 ++submitted;success=std::move(ok);failure=std::move(fail);return true;}
 std::expected<void,std::string> process_refresh_icon_step(system::core::AppContext&);
};
''' + actual + r'''
}
int main(){
 using namespace test;system::core::AppContext context;AppStoreApp app;app.context_=&context;
 assert(app.process_refresh_icon_step(context));assert(app.submitted==1);
 app.failure("Too many concurrent HTTP requests");
 if(app.refresh_icon_cursor_!=0 || app.advanced!=0 || app.scheduled!=1 || app.delay==0){
  fprintf(stderr,"FAIL: transient HTTP capacity rejection permanently discarded the icon\n");return 1;}
 assert(app.process_refresh_icon_step(context));assert(app.submitted==2);app.success(7);
 assert(app.refresh_icon_request_id_==7 && app.entries_[0].icon_request_id==7);
 AppStoreApp permanent;permanent.context_=&context;assert(permanent.process_refresh_icon_step(context));
 permanent.failure("HTTP service is not started");assert(permanent.advanced==1 && permanent.scheduled==0);
 AppStoreApp stopped;stopped.context_=&context;assert(stopped.process_refresh_icon_step(context));stopped.context_=nullptr;
 stopped.failure("Too many concurrent HTTP requests");assert(stopped.advanced==0 && stopped.scheduled==0);
}
'''
    with tempfile.TemporaryDirectory(prefix='espocket-store-icon-') as directory:
        path = Path(directory)/'test.cpp'; path.write_text(harness)
        binary = Path(directory)/'test'
        subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(path), '-o', str(binary)], check=True)
        return subprocess.run([str(binary)], capture_output=True, text=True, timeout=5)


class StoreIconAdmissionTest(unittest.TestCase):
    def test_transient_capacity_retains_icon_until_admitted(self):
        sys.path.insert(0, str(ROOT / 'scripts/firmware'))
        from prepare_patched_component import prepare
        baseline = run_control_flow(SOURCE)
        self.assertNotEqual(baseline.returncode, 0)
        self.assertIn('permanently discarded the icon', baseline.stderr)
        with tempfile.TemporaryDirectory(prefix='espocket-store-icon-patched-') as directory:
            patched = prepare(SOURCE, ROOT / 'firmware/patches/espressif__brookesia_app_store/0.8.2/manifest.json', Path(directory) / 'patched')
            result = run_control_flow(patched)
        self.assertEqual(result.returncode, 0, result.stderr)
