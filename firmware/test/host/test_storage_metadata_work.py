"""Count actual metadata queries and preserve file/directory/symlink results."""
from pathlib import Path
import subprocess
import tempfile
import unittest
import sys
ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'firmware/managed_components/espressif__brookesia_service_storage'

def run_flow(component, esp=False):
    source=(component/'src/service_storage.cpp').read_text()
    actual=source[source.index('uint64_t make_mtime_ms(') if 'uint64_t make_mtime_ms(' in source else source.index('StorageFileInfo make_file_info('):source.index('std::expected<size_t, std::string> read_file_to_buffer(')]
    harness=r'''
#include <filesystem>
#include <chrono>
#include <system_error>
#include <fstream>
#include <cassert>
#include <sys/stat.h>
#include <unistd.h>
namespace countedfs {
using path=std::filesystem::path; using file_time_type=std::filesystem::file_time_type;
using std::filesystem::exists; using std::filesystem::is_symlink; using std::filesystem::is_regular_file; using std::filesystem::is_directory;
inline unsigned queries=0;
auto symlink_status(const path&p,std::error_code&e){++queries;return std::filesystem::symlink_status(p,e);}
auto last_write_time(const path&p,std::error_code&e){++queries;return std::filesystem::last_write_time(p,e);}
auto file_size(const path&p,std::error_code&e){++queries;return std::filesystem::file_size(p,e);}
}
int counted_lstat(const char*p,struct stat*s){++countedfs::queries;return ::lstat(p,s);}
int counted_stat(const char*p,struct stat*s){++countedfs::queries;return ::stat(p,s);}
#define lstat counted_lstat
#define stat(...) counted_stat(__VA_ARGS__)
enum class StorageFileType{File,Directory,Other};
struct StorageFileInfo {bool exists=false; StorageFileType type=StorageFileType::Other; uint64_t size=0,mtime_ms=0;};
'''+actual.replace('std::filesystem::','countedfs::')+r'''
int main(int argc,char**argv){
 std::filesystem::path root=argv[1]; auto file=root/"file";std::ofstream(file)<<"abc";
 countedfs::queries=0;auto result=make_file_info(file);
 assert(result.exists && result.type==StorageFileType::File && result.size==3);
 std::error_code ec;auto expected=std::chrono::duration_cast<std::chrono::milliseconds>(std::filesystem::last_write_time(file,ec).time_since_epoch()).count();
 assert(result.mtime_ms==static_cast<uint64_t>(expected<0?0:expected));
 assert(countedfs::queries==1);
 auto dir=make_file_info(root);assert(dir.exists && dir.type==StorageFileType::Directory && dir.size==0);
 auto missing=make_file_info(root/"missing");assert(!missing.exists && missing.size==0 && missing.mtime_ms==0);
#if !defined(ESP_PLATFORM)
 std::filesystem::create_symlink(file,root/"link");auto link=make_file_info(root/"link");
 assert(link.exists && link.type==StorageFileType::Other && link.size==0 && link.mtime_ms==0);
 std::filesystem::create_symlink(root/"absent",root/"broken");auto broken=make_file_info(root/"broken");assert(broken.exists && broken.type==StorageFileType::Other);
#endif
}
'''
    with tempfile.TemporaryDirectory(prefix='espocket-storage-work-') as d:
        p=Path(d);(p/'main.cpp').write_text(harness)
        command=['c++','-std=c++23',str(p/'main.cpp'),'-o',str(p/'test')]
        if esp:command.insert(1,'-DESP_PLATFORM')
        subprocess.run(command,check=True,capture_output=True)
        return subprocess.run([str(p/'test'),str(p)],capture_output=True)

class StorageMetadataWork(unittest.TestCase):
    def test_upstream_repeats_metadata_queries(self):self.assertNotEqual(run_flow(SOURCE).returncode,0)
    def test_candidate_single_query_keeps_metadata(self):
        sys.path.insert(0,str(ROOT/'scripts/firmware'));from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory() as d:
            component=prepare(SOURCE,ROOT/'firmware/patches/espressif__brookesia_service_storage/0.8.3/manifest.json',Path(d)/'component')
            result=run_flow(component);self.assertEqual(result.returncode,0,result.stderr.decode())
    def test_esp_vfs_branch_uses_supported_single_stat(self):
        sys.path.insert(0,str(ROOT/'scripts/firmware'));from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory() as d:
            component=prepare(SOURCE,ROOT/'firmware/patches/espressif__brookesia_service_storage/0.8.3/manifest.json',Path(d)/'component')
            result=run_flow(component,esp=True);self.assertEqual(result.returncode,0,result.stderr.decode())
if __name__=='__main__':unittest.main()
