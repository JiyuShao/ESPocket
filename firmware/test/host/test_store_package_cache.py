"""Exercise successful Store installation and bounded, pinned package-cache eviction."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'firmware/managed_components/espressif__brookesia_app_store'


def run_install(component):
    text = (component / 'src/install/download.ipp').read_text()
    start = text.index('std::expected<void, std::string> AppStoreApp::install_package(')
    actual = text[start:text.index('void AppStoreApp::install_local_package(', start)]
    storage = (component / 'src/storage/storage.ipp').read_text()
    release = ''
    policy = ''
    if 'void AppStoreApp::release_installed_download_cache(' in storage:
        start = storage.index('bool AppStoreApp::is_owned_package_cache(')
        release = storage[start:storage.index('void AppStoreApp::reclaim_package_cache(', start)]
        start = storage.index('void AppStoreApp::reclaim_package_cache(')
        policy = storage[start:storage.index('void AppStoreApp::refresh_storage_capacity(', start)]
    else:
        release = 'void AppStoreApp::release_installed_download_cache(system::core::AppContext&,const std::filesystem::path&) {}'
    code = r'''
#include <algorithm>
#include <cassert>
#include <expected>
#include <filesystem>
#include <fstream>
#include <map>
#include <optional>
#include <string>
#include <vector>
#define BROOKESIA_LOGW(...) ((void)0)
namespace systemx::core {
struct PackageInstallOptions {};
enum class MessageDialogIcon {Warning,Information};
enum class MessageDialogButtonRole {Reject};
struct MessageDialogButton {std::string text;MessageDialogButtonRole role;};
struct Service {
 bool failed=false;
 std::expected<int,std::string> install_runtime_app_package(const std::string&path,bool){return install_runtime_app_package(path,PackageInstallOptions{});}
 std::expected<int,std::string> install_runtime_app_package(const std::string&,const PackageInstallOptions&){
  if(failed)return std::unexpected("injected install failure");return 1;
 }
};
struct AppContext {Service service;Service&system_service(){return service;}};
}
struct StorageHelper {
 enum class FileType {File};
 struct Info {bool exists; FileType type; uint64_t size,mtime_ms;};
 static std::expected<Info,std::string> fs_stat(const std::string&path){return Info{std::filesystem::exists(path),FileType::File,std::filesystem::file_size(path),0};}
 static std::expected<void,std::string> fs_remove(const std::string&path){std::filesystem::remove(path);return {};}
};
constexpr int INSTALL_SUCCESS_DIALOG_AUTO_CLOSE_MS=1500;
struct AppStoreApp {
 enum class MessageDialogPurpose {Install};
 struct Entry {std::filesystem::path cached_package_path;bool cached=true;uint64_t cached_package_size=42;std::filesystem::path download_path;bool downloading=false;};
 struct Local {std::filesystem::path package_path;std::string manifest_id,version;uint64_t file_size;};
 struct Operation {std::filesystem::path package_path;};
 std::vector<Entry> entries_;
 std::vector<Local> local_packages_;
 std::map<std::string,std::string> installed_version_by_manifest_id_;
 std::optional<Operation> developer_install_;
 std::vector<Operation> pending_deferred_operations_;
 bool storage_capacity_known_=true;
 uint64_t storage_free_bytes_=1ULL<<30;
 std::filesystem::path cache;
 std::string status_text_;
 std::vector<std::filesystem::path> download_dirs(systemx::core::AppContext&)const{return {cache/"apps"};}
 bool is_owned_package_cache(systemx::core::AppContext&,const std::filesystem::path&)const;
 void release_abandoned_partial_cache(systemx::core::AppContext&,const std::filesystem::path&);
 void release_installed_download_cache(systemx::core::AppContext&,const std::filesystem::path&);
 void reclaim_package_cache(systemx::core::AppContext&,uint64_t,const std::filesystem::path& = {});
 bool read_package_cache_capacity(auto&){return storage_capacity_known_;}
 void rebuild_local_package_index(){}
 void prefer_external_install_storage(auto&){}
 void refresh_installed_apps(auto&){}
 void start_local_package_scan(auto&,bool){}
 void refresh_storage_capacity(auto&){}
 void populate_entries(auto&){}
 std::string tr(const char*text){return text;}
 void ensure_message_dialog(systemx::core::AppContext&,std::string,std::string,systemx::core::MessageDialogIcon,int,MessageDialogPurpose,std::vector<systemx::core::MessageDialogButton> = {}){}
 std::expected<void,std::string> install_package(systemx::core::AppContext&,const std::filesystem::path&,std::string_view,const systemx::core::PackageInstallOptions&);
 std::expected<void,std::string> install_package(systemx::core::AppContext&,const std::filesystem::path&,std::string_view);
};
int compare_versions(const std::string&left,const std::string&right){return left.compare(right);}
''' + actual.replace('system::core', 'systemx::core') + release.replace('system::core', 'systemx::core') + policy.replace('system::core', 'systemx::core') + r'''
int main(int argc,char**argv){
 assert(argc==2);namespace fs=std::filesystem;
 AppStoreApp app;app.cache=fs::path(argv[1])/"store/cache";
 const auto cached=app.cache/"apps/example.app/1.0.0.bpk";
 const auto original=fs::path(argv[1])/"apps/example.app/.brookesia-package.bpk";
 const auto user=fs::path(argv[1])/"imports/manual.bpk";
 for(const auto&path:{cached,original,user}){fs::create_directories(path.parent_path());std::ofstream(path)<<"package bytes";}
 app.entries_.push_back({cached});systemx::core::AppContext context;
 context.service.failed=true;assert(!app.install_package(context,cached,"Example",{}));assert(fs::exists(cached));
 context.service.failed=false;assert(app.install_package(context,cached,"Example",{}));
 assert(!fs::exists(cached));assert(fs::exists(original));assert(fs::exists(user));assert(!app.entries_[0].cached);
 assert(app.install_package(context,user,"Manual",{}));assert(fs::exists(user));
 PARTIAL_TEST
 POLICY_TEST
}
'''
    if policy:
        code = code.replace('PARTIAL_TEST', r'''
 const auto partial=app.cache/"apps/example.app/1.1.bpk.part";
 const auto manual=fs::path(argv[1])/"imports/manual.bpk.part";
 for(const auto&path:{partial,manual}){fs::create_directories(path.parent_path());std::ofstream(path)<<"partial bytes";}
 app.entries_.push_back({{},false,0,partial,true});
 app.release_abandoned_partial_cache(context,partial);assert(fs::exists(partial));
 app.entries_.back().downloading=false;
 app.release_abandoned_partial_cache(context,partial);assert(!fs::exists(partial));
 app.release_abandoned_partial_cache(context,manual);assert(fs::exists(manual));
 ''')
        code = code.replace('POLICY_TEST', r'''
 const auto first=app.cache/"apps/first/1.0.bpk",second=app.cache/"apps/second/1.0.bpk";
 const auto third=app.cache/"apps/third/1.0.bpk",redundant=app.cache/"apps/redundant/1.0.bpk";
 for(const auto&path:{first,second,third,redundant}){fs::create_directories(path.parent_path());std::ofstream(path)<<std::string(256*1024,'p');app.local_packages_.push_back({path,path.parent_path().filename().string(),"1.0",256*1024});}
 app.installed_version_by_manifest_id_["redundant"]="2.0";
 app.developer_install_=AppStoreApp::Operation{first};app.pending_deferred_operations_.push_back({second});
 app.reclaim_package_cache(context,0);assert(fs::exists(first) && fs::exists(second));
 assert(!fs::exists(redundant) && !fs::exists(third));assert(fs::exists(original) && fs::exists(user));
 assert(app.local_packages_.size()==2);
 app.developer_install_.reset();app.pending_deferred_operations_.clear();
 app.entries_.push_back({first,true,256*1024,first,true});
 app.storage_free_bytes_=0;app.reclaim_package_cache(context,128*1024);
 assert(fs::exists(first) && !fs::exists(second));
 assert(fs::exists(original) && fs::exists(user));
''')
    else:
        code = code.replace('POLICY_TEST', '').replace('PARTIAL_TEST', '')
    if 'const system::core::PackageInstallOptions &options' not in actual:
        code = code.replace('app.install_package(context,cached,"Example",{})', 'app.install_package(context,cached,"Example")').replace('app.install_package(context,user,"Manual",{})', 'app.install_package(context,user,"Manual")')
    with tempfile.TemporaryDirectory(prefix='store-cache-install-') as directory:
        source = Path(directory) / 'test.cpp'
        source.write_text(code)
        executable = Path(directory) / 'test'
        result = subprocess.run(['c++', '-std=c++23', str(source), '-o', str(executable)], capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stderr.decode())
        return subprocess.run([str(executable), directory], capture_output=True)


class StorePackageCacheTest(unittest.TestCase):
    def test_original_keeps_duplicate_after_success(self):
        self.assertNotEqual(run_install(SOURCE).returncode, 0)

    def test_candidate_reclaims_only_after_committed_install(self):
        sys.path.insert(0, str(ROOT / 'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='store-cache-component-') as directory:
            component = prepare(SOURCE, ROOT / 'firmware/patches/espressif__brookesia_app_store/0.8.2/manifest.json', Path(directory) / 'component')
            result = run_install(component)
            self.assertEqual(result.returncode, 0, result.stderr.decode())


if __name__ == '__main__':
    unittest.main()
