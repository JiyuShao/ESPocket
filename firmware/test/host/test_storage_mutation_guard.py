"""Execute all real Storage mutation entry points with guard denial and success."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[3]

HARNESS=r'''
#include <filesystem>
#include <expected>
#include <string>
#include <fstream>
#include <vector>
#include <cassert>
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS(...)
#define BROOKESIA_LOGD(...)
struct RawBuffer {const void *data;size_t data_size;template<class T>const T*to_const_ptr()const{return static_cast<const T*>(data);}};
using Path=std::filesystem::path;
using Result=std::expected<void,std::string>;
static unsigned side_effects=0;
Result create_directory_tree(const Path&p){++side_effects;std::filesystem::create_directories(p);return {};}
Result ensure_parent_directory(const Path&p){return create_directory_tree(p.parent_path());}
Result write_bytes_to_file(const Path&p,const uint8_t*b,size_t n){++side_effects;std::ofstream f(p,std::ios::binary);f.write(reinterpret_cast<const char*>(b),n);return {};}
Result remove_path_tree(const Path&p){++side_effects;std::filesystem::remove_all(p);return {};}
Result copy_path_tree(const Path&a,const Path&b,bool){++side_effects;std::filesystem::copy(a,b,std::filesystem::copy_options::recursive|std::filesystem::copy_options::overwrite_existing);return {};}
bool is_file_system_root(const std::vector<Path>&,const Path&){return false;}
struct Storage {
 bool fs_iface_=true;std::vector<Path>file_system_roots_;std::vector<Path> authorized;Path denied;
 std::expected<Path,std::string>resolve_file_system_path(const std::string&p){return Path(p).lexically_normal();}
 Result authorize_file_system_mutation(const Path&p){authorized.push_back(p);if(p==denied)return std::unexpected("denied");return {};}
 Result function_fs_mkdir(const std::string&);
 Result function_fs_write_text(const std::string&,const std::string&);
 Result function_fs_write(const std::string&,const RawBuffer&);
 Result function_fs_remove(const std::string&);
 Result function_fs_rename(const std::string&,const std::string&);
 Result function_fs_copy_tree(const std::string&,const std::string&,bool);
};
'''
MAIN=r'''
int main(int,char**argv){
 Path root=argv[1],src=root/"src",dst=root/"dst";std::ofstream(src)<<"original";
 Storage storage;storage.denied=dst;
 auto blocked=[&](auto operation){storage.authorized.clear();side_effects=0;auto result=operation();assert(!result && result.error()=="denied" && !side_effects);assert(storage.authorized.back()==dst);};
 blocked([&]{return storage.function_fs_mkdir(dst.string());});
 blocked([&]{return storage.function_fs_write_text(dst.string(),"bad");});
 const char bytes[]="bad";RawBuffer buffer{bytes,3};
 blocked([&]{return storage.function_fs_write(dst.string(),buffer);});
 blocked([&]{return storage.function_fs_remove(dst.string());});
 blocked([&]{return storage.function_fs_rename(src.string(),dst.string());});
 blocked([&]{return storage.function_fs_copy_tree(src.string(),dst.string(),true);});
 assert(std::filesystem::exists(src) && !std::filesystem::exists(dst));
 storage.denied=src;side_effects=0;assert(!storage.function_fs_rename(src.string(),dst.string()));assert(!side_effects && std::filesystem::exists(src));
 storage.denied.clear();assert(storage.function_fs_write_text(dst.string(),"allowed"));
 assert(storage.function_fs_write(dst.string(),buffer));assert(storage.function_fs_remove(dst.string()));
 assert(storage.function_fs_copy_tree(src.string(),dst.string(),true));assert(storage.function_fs_remove(dst.string()));
 assert(storage.function_fs_rename(src.string(),dst.string()));assert(!std::filesystem::exists(src));
 assert(storage.function_fs_mkdir((root/"directory").string()));
}
'''

class StorageMutationGuardTest(unittest.TestCase):
    def test_actual_storage_calls_guard_before_any_mutation(self):
        sys.path.insert(0,str(ROOT/'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='espocket-storage-guard-') as directory:
            root=Path(directory)
            component=prepare(ROOT/'firmware/managed_components/espressif__brookesia_service_storage',ROOT/'firmware/patches/espressif__brookesia_service_storage/0.8.3/manifest.json',root/'component')
            source=(component/'src/service_storage.cpp').read_text()
            actual=[]
            for name in ('mkdir','write_text','write','remove','rename','copy_tree'):
                method=source.index('Storage::function_fs_'+name+'(')
                start=source.rfind('\nstd::expected<',0,method)+1
                end=source.index('\nstd::expected<',method)
                actual.append(source[start:end])
            harness=root/'main.cpp';harness.write_text(HARNESS+'\n'.join(actual)+MAIN)
            binary=root/'test'
            compiled=subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23',str(harness),'-o',str(binary)],capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            result=subprocess.run([str(binary),str(root)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)

KV_HARNESS=r'''
#include <expected>
#include <string>
#include <vector>
#include <cassert>
#include <boost/json/src.hpp>
#include <boost/format.hpp>
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS(...)
#define BROOKESIA_LOGD(...)
#define BROOKESIA_DESCRIBE_FROM_JSON(a,b) ((b=(a)),true)
#define BROOKESIA_DESCRIBE_TO_STR(...) std::string("redacted")
struct Entry {};
boost::json::value as_json(const std::vector<Entry>&){return boost::json::array{};}
boost::json::value as_json(const boost::json::object&o){return o;}
#define BROOKESIA_DESCRIBE_TO_JSON(a) as_json(a)
using KeyValueMap=boost::json::object;
struct StorageKvIface {
 using EntryInfo=Entry;unsigned calls=0;boost::json::object values;
 bool list(const std::string&,std::vector<Entry>&){++calls;return true;}
 bool set(const std::string&,const KeyValueMap&v){++calls;values=v;return true;}
 bool get(const std::string&,const std::vector<std::string>&,KeyValueMap&v){++calls;v=values;return true;}
 bool erase(const std::string&,const std::vector<std::string>&){++calls;values.clear();return true;}
};
std::string get_last_error_or_default(const StorageKvIface&,const std::string&s){return s;}
std::vector<std::string>parse_keys(const boost::json::array&v){return v.empty()?std::vector<std::string>{}:std::vector<std::string>{"key"};}
struct Storage {
 StorageKvIface backend;StorageKvIface*kv_iface_=&backend;bool native=false;
 std::expected<void,std::string>authorize_key_value_access(const std::string&nspace){if(nspace=="core.pkg.v2"&&!native)return std::unexpected("private");return {};}
 std::expected<boost::json::array,std::string>function_list(const std::string&);
 std::expected<void,std::string>function_set(const std::string&,boost::json::object&&);
 std::expected<boost::json::object,std::string>function_get(const std::string&,boost::json::array&&);
 std::expected<void,std::string>function_erase(const std::string&,boost::json::array&&);
};
'''
KV_MAIN=r'''
int main(){
 Storage s;
 assert(!s.function_list("core.pkg.v2"));assert(!s.function_get("core.pkg.v2",{}));
 assert(!s.function_set("core.pkg.v2",{{"key","fake"}}));assert(!s.function_erase("core.pkg.v2",{}));assert(!s.backend.calls);
 assert(s.function_set("ordinary",{{"key","data"}}));assert(s.function_get("ordinary",{}));
 s.native=true;assert(s.function_set("core.pkg.v2",{{"key","local"}}));assert(s.function_get("core.pkg.v2",{}));assert(s.function_list("core.pkg.v2"));assert(s.function_erase("core.pkg.v2",{}));
}
'''

class StoragePrivateKvGuardTest(unittest.TestCase):
    def test_actual_kv_entries_guard_reads_and_writes(self):
        sys.path.insert(0,str(ROOT/'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='espocket-storage-kv-guard-') as directory:
            root=Path(directory)
            component=prepare(ROOT/'firmware/managed_components/espressif__brookesia_service_storage',ROOT/'firmware/patches/espressif__brookesia_service_storage/0.8.3/manifest.json',root/'component')
            source=(component/'src/service_storage.cpp').read_text()
            actual=[]
            for name in ('list','set','get','erase'):
                method=source.index('Storage::function_'+name+'(')
                start=source.rfind('\nstd::expected<',0,method)+1
                end=source.index('\nstd::expected<',method)
                actual.append(source[start:end])
            harness=root/'main.cpp';harness.write_text(KV_HARNESS+'\n'.join(actual)+KV_MAIN)
            binary=root/'test'
            compiled=subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23','-DBOOST_NO_USER_CONFIG','-I'+str(ROOT/'firmware/managed_components/espressif__esp-boost/src'),str(harness),'-o',str(binary)],capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
