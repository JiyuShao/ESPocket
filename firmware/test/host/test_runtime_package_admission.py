"""Execute patched Core package parsing, admission, receipts and reboot recovery.

The filesystem service is an on-disk host Adapter. SHA-256 uses the host crypto
library; device builds use mbedTLS. Release verification is injected as failing:
this suite proves no fallback from signed failures, not RSA implementation.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / 'firmware/managed_components/espressif__brookesia_system_core'

TYPES = r'''
#pragma once
#include <expected>
#include <functional>
#include <map>
#include <string>
#include <vector>
#include <cstdint>
namespace esp_brookesia {
namespace runtime {
enum class BackendType { Unknown, JavaScript, Lua, Wasm };
struct AppConfig { BackendType type; std::string app_path,entry,resource_dir; std::vector<std::string> arguments; };
}
namespace gui { enum class MountStackMode { Replace, Max }; }
namespace system::core {
enum class AppKind { Native, Runtime };
enum class GuiAppLayer { AppDefault, AppTop, SystemBottom, SystemTop };
enum class GuiRootKind { None, File };
struct AppManifestService {std::string name,version;};
struct GuiScreenFlowEntry {std::string screen_flow; GuiAppLayer layer; gui::MountStackMode mount_mode; int32_t z_order;};
struct AppGuiResources {};
struct AppGuiDescriptor {GuiRootKind root_kind; std::string root; AppGuiResources resources; std::vector<GuiScreenFlowEntry> screen_flows;};
struct RuntimeAppResourceDescriptor {std::string icon_id; bool preload_dom; AppGuiDescriptor gui;};
struct AppManifest {
 std::string id,name,version,app_path,entry,resource_dir,icon_id;
 AppKind kind=AppKind::Runtime; bool visible=true,preload_dom=false;
 std::map<std::string,std::string> localized_names;
 std::vector<std::string> supported_systems,arguments;
 std::vector<AppManifestService> services;
 runtime::BackendType runtime_type=runtime::BackendType::Unknown;
};
inline std::string resolve_app_display_name(const AppManifest &m,const char*) {return m.localized_names.empty()?m.id:m.localized_names.begin()->second;}
inline void normalize_app_manifest(AppManifest&) {}
}
}
inline bool host_enum(const std::string&s,esp_brookesia::runtime::BackendType&v) {
 if(s=="JavaScript"){v=esp_brookesia::runtime::BackendType::JavaScript;return true;}
 if(s=="Lua"){v=esp_brookesia::runtime::BackendType::Lua;return true;}return false;}
inline bool host_enum(const std::string&s,esp_brookesia::gui::MountStackMode&v){return s=="Replace";}
inline bool host_enum(const std::string&s,esp_brookesia::system::core::GuiAppLayer&v){return s=="AppDefault";}
#define BROOKESIA_DESCRIBE_STR_TO_ENUM_FLEXIBLE(s,v) host_enum(s,v)
'''
CALL_CONTEXT = r'''
#pragma once
#include <map>
#include <string>
#include <utility>
namespace esp_brookesia::service {
using CallContext=std::map<std::string,std::string>;
inline thread_local CallContext current_context;
inline CallContext get_current_call_context(){return current_context;}
class ScopedCallContext {
 CallContext prior;
public:
 explicit ScopedCallContext(CallContext value):prior(std::move(current_context)){current_context=std::move(value);}
 ~ScopedCallContext(){current_context=std::move(prior);}
};
}
'''
STORAGE_GUARD = r'''
#pragma once
#include <functional>
#include <filesystem>
#include <expected>
#include "brookesia/service_manager/common.hpp"
namespace esp_brookesia::service {
using MutationGuard=std::function<std::expected<void,std::string>(const std::filesystem::path&,const CallContext&)>;
inline MutationGuard storage_guard;
using KvGuard=std::function<std::expected<void,std::string>(const std::string&,const CallContext&)>;
inline KvGuard kv_guard;
struct Storage {
 static Storage &get_instance(){static Storage instance;return instance;}
 void set_file_system_mutation_guard(MutationGuard guard){storage_guard=std::move(guard);}
 void set_key_value_access_guard(KvGuard guard){kv_guard=std::move(guard);}
};
inline std::expected<void,std::string> guard_write(const std::string &path){
 if(storage_guard)return storage_guard(std::filesystem::path(path),get_current_call_context());return {};
}
}
'''

STORAGE = r'''
#pragma once
#include <filesystem>
#include <fstream>
#include <expected>
#include <vector>
#include <iterator>
#include <cassert>
#include "brookesia/service_storage.hpp"
#include <boost/json.hpp>
namespace esp_brookesia::service {
struct RawBuffer { uint8_t *data; size_t size; RawBuffer(uint8_t*p,size_t n):data(p),size(n){} };
namespace helper {
struct Timeout {explicit Timeout(unsigned){}};
struct Storage {
 enum class FunctionId {KVGet,KVSet,GetFileSystems,GetFileSystemCapacity};
 static inline uint64_t capacity_free_bytes = 1ULL << 30;
 static inline bool capacity_unknown = false;
 template<class T> static std::expected<T,std::string> call_function_sync(FunctionId,Timeout){
  if(capacity_unknown)return std::unexpected("injected capacity failure");
  return boost::json::array{boost::json::object{{"mount_point","/"},{"root_path","/"}}};
 }
 template<class T> static std::expected<T,std::string> call_function_sync(FunctionId,const std::string&,Timeout){
  return boost::json::object{{"free_bytes",capacity_free_bytes}};
 }
 static inline unsigned write_wait_ms = 0;
 using Timeout=helper::Timeout;
 static inline boost::json::object kv_values;
 template<class T,class V> static std::expected<T,std::string> call_function_sync(FunctionId id,const std::string&nspace,V values,Timeout){
  if(kv_guard){auto allowed=kv_guard(nspace,get_current_call_context());if(!allowed)return std::unexpected(allowed.error());}
  if constexpr(std::is_same_v<T,void>){assert(id==FunctionId::KVSet);kv_values=values;return {};}
  else {assert(id==FunctionId::KVGet);return kv_values;}
 }
 enum class FileType {File,Directory,Other};
 struct Info {bool exists; FileType type; uint64_t size;};
 struct Entry {std::string name;Info info;};
 static inline std::string fail_remove_to,fail_rename_to,fail_next_rename_to;
 static inline unsigned directory_scans=0,binary_reads=0;
 static void reset_counts(){directory_scans=0;binary_reads=0;}
 static std::expected<void,std::string> fs_copy_tree(const std::string&a,const std::string&b,bool overwrite,unsigned){auto g=guard_write(b);if(!g)return g;std::error_code ec;std::filesystem::create_directories(b);std::filesystem::copy(a,b,std::filesystem::copy_options::recursive|(overwrite?std::filesystem::copy_options::overwrite_existing:std::filesystem::copy_options::skip_existing),ec);if(ec)return std::unexpected(ec.message());return {};}
 static std::expected<Info,std::string> fs_stat(const std::string&p,unsigned){
  std::error_code ec;auto status=std::filesystem::symlink_status(p,ec);
  if(ec && ec!=std::errc::no_such_file_or_directory)return std::unexpected(ec.message());
  bool exists=std::filesystem::exists(status); auto type=std::filesystem::is_directory(status)?FileType::Directory:std::filesystem::is_regular_file(status)?FileType::File:FileType::Other;
  return Info{exists,type,exists&&type==FileType::File?std::filesystem::file_size(p):0};}
 static std::expected<void,std::string> fs_mkdir(const std::string&p,unsigned){auto g=guard_write(p);if(!g)return g;std::filesystem::create_directories(p);return {};}
 static std::expected<std::string,std::string> fs_read_text(const std::string&p,unsigned){std::ifstream f(p,std::ios::binary);if(!f)return std::unexpected("missing");return std::string(std::istreambuf_iterator<char>(f),{});}
 static std::expected<size_t,std::string> fs_read(const std::string&p,RawBuffer b,unsigned){++binary_reads;std::ifstream f(p,std::ios::binary);if(!f)return std::unexpected("missing");f.read(reinterpret_cast<char*>(b.data),b.size);return f.gcount();}
 static std::expected<void,std::string> fs_write(const std::string&p,RawBuffer b,unsigned timeout){if(timeout<write_wait_ms)return std::unexpected("injected write timeout");auto g=guard_write(p);if(!g)return std::unexpected(g.error());std::ofstream f(p,std::ios::binary);f.write(reinterpret_cast<char*>(b.data),b.size);if(!f)return std::unexpected("write failed");return {};}
 static std::expected<void,std::string> fs_write_text(const std::string&p,const std::string&s,unsigned){auto g=guard_write(p);if(!g)return g;std::ofstream f(p,std::ios::binary);f<<s;if(!f)return std::unexpected("write failed");return {};}
 static std::expected<std::vector<Entry>,std::string> fs_list(const std::string&p,unsigned){++directory_scans;std::error_code ec;std::filesystem::directory_iterator it(p,ec);if(ec)return std::unexpected(ec.message());std::vector<Entry> v;for(auto&e:it)v.push_back({e.path().filename().string(),*fs_stat(e.path().string(),0)});return v;}
 static std::expected<void,std::string> fs_remove(const std::string&p,unsigned){auto g=guard_write(p);if(!g)return g;if(p==fail_remove_to)return std::unexpected("injected remove failure");std::error_code ec;std::filesystem::remove_all(p,ec);if(ec)return std::unexpected(ec.message());return {};}
 static std::expected<void,std::string> fs_rename(const std::string&a,const std::string&b,unsigned){auto g=guard_write(b);if(!g)return g;g=guard_write(a);if(!g)return g;if(b==fail_next_rename_to){fail_next_rename_to.clear();return std::unexpected("one-shot rename failure");}if(b==fail_rename_to)return std::unexpected("injected rename failure");std::error_code ec;std::filesystem::rename(a,b,ec);if(ec)return std::unexpected(ec.message());return {};}
};
}}
'''
TRANSACTION_ADAPTER = r'''
namespace esp_brookesia::system::core {
constexpr unsigned STORAGE_FS_TIMEOUT_MS=0;
constexpr int SYSTEM_APP_TASK_GROUP=0;
enum class AppState {Installed,Running,Paused};
using AppId=uint32_t;
struct AppInfo {AppId app_id;AppManifest manifest;AppState state=AppState::Installed;};
struct System {
 struct Impl {
  RuntimePackagePolicy package_policy_; bool package_transaction_=false;
  bool should_schedule_app_task(){return false;}
  template<class T,class F> T run_task_sync(int,F f,T){return f();}
 };
 Impl storage;Impl*impl_=&storage;
 std::filesystem::path root;
 std::vector<AppInfo> apps;uint32_t next=1;std::string fail_install_version;bool fail_stop=false;
 bool replacement_prepared=false,replacement_rolled_back=false,replacement_committed=false,fail_replacement_commit=false;
 std::string get_system_type()const{return "espocket";}
 auto get_storage_layout()const{return root;}
 auto list_apps()const{return apps;}
 std::optional<AppInfo> get_app(AppId id)const{for(const auto&a:apps)if(a.app_id==id)return a;return {};}
 std::expected<AppId,std::string> install_runtime_app_package(std::string_view,bool);
 std::expected<AppId,std::string> install_runtime_app_package(std::string_view,const PackageInstallOptions&);
 std::expected<PackageAdmission,std::string> inspect_runtime_package(std::string_view p,std::string_view hash={})const{return core::inspect_runtime_package(p,get_system_type(),impl_->package_policy_,hash);}
 std::expected<void,std::string> stop_app(AppId id){if(fail_stop)return std::unexpected("stop failure");for(auto&a:apps)if(a.app_id==id)a.state=AppState::Installed;return {};}
 std::expected<void,std::string> detach_app_for_replacement(AppId id){for(auto it=apps.begin();it!=apps.end();++it)if(it->app_id==id){apps.erase(it);return {};}return std::unexpected("not installed");}
 void on_app_replacement_prepared(const AppInfo&){replacement_prepared=true;replacement_rolled_back=false;replacement_committed=false;}
 std::expected<void,std::string> on_app_replaced(const AppInfo&,const AppInfo&){return {};}
 std::expected<void,std::string> on_app_replacement_committed(const AppInfo&,const AppInfo&){replacement_committed=true;if(fail_replacement_commit)return std::unexpected("writer failure");return {};}
 std::expected<void,std::string> on_app_replacement_rolled_back(const AppInfo&,const AppInfo&){replacement_rolled_back=true;return {};}
 std::expected<AppId,std::string> install_runtime_app(const AppManifest&m){
  auto admitted=validate_installed_runtime_package(m.app_path,get_system_type(),impl_->package_policy_,false,impl_->package_transaction_);
  if(!admitted)return std::unexpected(admitted.error());
  if(m.version==fail_install_version)return std::unexpected("activation failure");
  auto id=next++;apps.push_back({id,m});return id;}
};
bool is_safe_app_directory_name(std::string_view s){return s.find('/')==s.npos && s.find('\\')==s.npos && !s.empty();}
std::optional<AppInfo> find_app_by_manifest_id(const System&s,std::string_view id){for(auto&a:s.apps)if(a.manifest.id==id)return a;return {};}
std::string make_unique_install_directory_name(std::string_view s){static int n=0;return std::string(s)+std::to_string(++n);}
std::expected<std::filesystem::path,std::string> get_default_install_app_root(const std::filesystem::path&p){return p;}
std::expected<void,std::string> check_runtime_app_service_requirements(const AppManifest&,const char*){return {};}
'''

TRANSACTION_MATRIX = r'''
{
 using namespace esp_brookesia::system::core;
 System sys;sys.root=root/"transactions";sys.impl_->package_policy_=p;
 PackageInstallOptions options;options.developer_confirmed=true;
 assert(!sys.install_runtime_app_package((root/"super.bpk").string(),true));
 Storage::capacity_free_bytes=0;
 auto no_space=sys.install_runtime_app_package((root/"super.bpk").string(),options);
 assert(!no_space && no_space.error()=="insufficient_install_space");assert(sys.apps.empty());
 Storage::capacity_free_bytes=1ULL<<30;Storage::capacity_unknown=true;
 auto unavailable=sys.install_runtime_app_package((root/"super.bpk").string(),options);
 assert(!unavailable && unavailable.error()=="install_capacity_unavailable");assert(sys.apps.empty());
 Storage::capacity_unknown=false;
 auto first=sys.install_runtime_app_package((root/"super.bpk").string(),options);
 if(!first){std::cerr<<first.error();return 1;}
 const auto installed=sys.root/"test.game";
 fs::create_directories(installed/"data");std::ofstream(installed/"data/private")<<"keep";
 options.expected_sha256=std::string(64,'0');assert(!sys.install_runtime_app_package((root/"update.bpk").string(),options));options.expected_sha256.clear();
 options.expected_id="another.app";assert(!sys.install_runtime_app_package((root/"update.bpk").string(),options));options.expected_id.clear();
 sys.fail_install_version="2.0.0";assert(!sys.install_runtime_app_package((root/"update.bpk").string(),options));
 assert(sys.replacement_prepared && sys.replacement_rolled_back && !sys.replacement_committed);
 if(!(sys.apps.size()==1 && sys.apps[0].manifest.version=="1.0.0" && fs::exists(installed/"data/private"))){std::cerr<<" rollback state apps="<<sys.apps.size()<<" private="<<fs::exists(installed/"data/private");if(!sys.apps.empty())std::cerr<<" version="<<sys.apps[0].manifest.version;return 3;}sys.fail_install_version.clear();
 Storage::fail_next_rename_to=installed.string();assert(!sys.install_runtime_app_package((root/"update.bpk").string(),options));
 assert(sys.apps.size()==1 && sys.apps[0].manifest.version=="1.0.0" && fs::exists(installed/"data/private"));
 Storage::fail_next_rename_to=(installed/".brookesia-install.json").string();assert(!sys.install_runtime_app_package((root/"update.bpk").string(),options));
 assert(sys.apps.size()==1 && sys.apps[0].manifest.version=="1.0.0" && fs::exists(installed/"data/private"));
 sys.apps[0].state=AppState::Running;sys.fail_stop=true;assert(!sys.install_runtime_app_package((root/"update.bpk").string(),options));
 assert(sys.apps[0].state==AppState::Running && fs::exists(installed/"data/private"));sys.fail_stop=false;
 auto updated=sys.install_runtime_app_package((root/"update.bpk").string(),options);assert(updated);
 assert(sys.replacement_prepared && !sys.replacement_rolled_back && sys.replacement_committed);
 assert(sys.apps.size()==1 && sys.apps[0].manifest.version=="2.0.0" && fs::exists(installed/"data/private"));
 assert(!fs::exists(sys.root/".rollback/test.game"));
 assert(validate_installed_runtime_package(installed.string(),"espocket",p));
 sys.fail_replacement_commit=true;
 auto postcommit_failed=sys.install_runtime_app_package((root/"update2.bpk").string(),options);assert(!postcommit_failed);
 assert(postcommit_failed.error().find("committed_package_card_persistence_failed: writer failure")!=std::string::npos);
 assert(sys.apps.size()==1 && sys.apps[0].manifest.version=="3.0.0");
 assert(fs::exists(sys.root/".rollback/test.game") && sys.replacement_committed && !sys.replacement_rolled_back);
 assert(validate_installed_runtime_package(installed.string(),"espocket",p));
 sys.fail_replacement_commit=false;
 fs::remove_all(sys.root/".rollback/test.game");
 sys.fail_install_version="3.0.0";Storage::fail_remove_to=installed.string();
 auto cleanup_failed=sys.install_runtime_app_package((root/"update2.bpk").string(),options);assert(!cleanup_failed);
 assert(cleanup_failed.error().find("rollback_cleanup_failed:")!=std::string::npos);
 assert(cleanup_failed.error().find("injected remove failure")!=std::string::npos);
 const auto retained=sys.root/".rollback/test.game";
 assert(fs::exists(retained/"data/private") && fs::exists(installed));
 assert(validate_installed_runtime_package(retained.string(),"espocket",p,false));
 Storage::fail_remove_to.clear();
}
'''


CACHE_MATRIX = r'''
{
 // The real wrapper/guard run against an on-disk Storage Adapter. Only package
 // directory scans and binary member/BPK reads are counted as full work.
 using namespace esp_brookesia::system::core;
 const auto cache_root=root/"protected-apps", cached=cache_root/"test.game";
 fs::create_directories(cache_root);fs::copy(final,cached,fs::copy_options::recursive);
 RuntimePackagePolicy cp=p;cp.public_key_pem_path.clear();cp.reuse_verified_installations=true;
 assert(!validate_installed_runtime_package(cached.string(),"espocket",cp));
 auto reboot=[&]{cp.validation_state.reset();assert(initialize_runtime_package_validation(cp,{cache_root.string()}));};
 auto validate=[&](bool start=true){auto result=validate_installed_runtime_package(cached.string(),"espocket",cp,start);if(!result)std::cerr<<"cache validation: "<<result.error()<<"\n";return result;};
 const auto seal=cached/".brookesia-verified.json", temporary=cached/".brookesia-verified.pending";
 reboot();
 // A forged pre-migration record cannot acquire trust.
 std::ofstream(seal)<<"{\"format\":\"core.package.validation.v2\",\"unsigned\":false}";
 Storage::reset_counts();assert(validate());assert(Storage::directory_scans && Storage::binary_reads);
 assert(fs::exists(seal));
 // Independent system HMAC implementation checks the generated record MAC.
 auto authenticated=boost::json::parse(*Storage::fs_read_text(seal.string(),0)).as_object();
 auto actual_mac=std::string(authenticated.at("mac").as_string());authenticated.erase("mac");
 auto key=std::string(Storage::kv_values.at("seal_key").as_string());auto payload=boost::json::serialize(authenticated);unsigned char expected_mac[32];
 assert(!host_hmac(reinterpret_cast<const unsigned char*>(key.data()),key.size(),reinterpret_cast<const unsigned char*>(payload.data()),payload.size(),expected_mac));
 constexpr char hex[]="0123456789abcdef";std::string mac;for(auto byte:expected_mac){mac+=hex[byte>>4];mac+=hex[byte&15];}assert(actual_mac==mac);
 auto admitted=validate();assert(admitted && admitted->transaction_identity==std::string(receipt_json.at("transaction").as_string()));
 for(int i=0;i<3;++i){Storage::reset_counts();assert(validate());assert(!Storage::directory_scans && !Storage::binary_reads);}
 // Cold state reads authenticated metadata, not package content.
 reboot();Storage::reset_counts();assert(validate());assert(!Storage::directory_scans && !Storage::binary_reads);
 developer=false;Storage::reset_counts();assert(!validate());assert(!Storage::directory_scans && !Storage::binary_reads);assert(validate(false));developer=true;
 assert(!Storage::call_function_sync<boost::json::object>(Storage::FunctionId::KVGet,"core.pkg.v2",boost::json::array{"seal_key"},Storage::Timeout(0)));
 assert(!Storage::call_function_sync<void>(Storage::FunctionId::KVSet,"core.pkg.v2",boost::json::object{{"seal_key","fake"}},Storage::Timeout(0)));
 for(const auto &dir:{"data","cache","files"}){
  assert(Storage::fs_mkdir((cached/dir).string(),0));assert(Storage::fs_write_text((cached/dir/"private").string(),"keep",0));
  Storage::reset_counts();assert(validate());assert(!Storage::directory_scans && !Storage::binary_reads);
 }
 const auto code=cached/"app/app.js";auto source=*Storage::fs_read_text(code.string(),0);
 assert(!Storage::fs_write_text(code.string(),"bad",0));
 unsigned char byte='x';assert(!Storage::fs_write(code.string(),{&byte,1},0));
 assert(!Storage::fs_mkdir((cached/"res/new").string(),0));
 assert(!Storage::fs_remove((cached/"res").string(),0));
 assert(!Storage::fs_rename(code.string(),(cached/"data/code").string(),0));
 assert(!Storage::fs_rename((cached/"data/private").string(),code.string(),0));
 assert(!Storage::fs_copy_tree((cached/"data").string(),(cached/"res").string(),true,0));
 assert(!Storage::fs_write_text(seal.string(),"{}",0));assert(!Storage::fs_remove(cache_root.string(),0));
 assert(*Storage::fs_read_text(code.string(),0)==source && fs::exists(seal));
 {
  detail::PackageMutationScope mutation(cp);assert(Storage::fs_write_text(code.string(),"bad",0));
 }
 assert(!fs::exists(seal) && !is_runtime_package_validation_current(cached.string(),cp));
 reboot();assert(!validate());
 {detail::PackageMutationScope mutation(cp);assert(Storage::fs_write_text(code.string(),source,0));}
 Storage::reset_counts();assert(validate());assert(Storage::directory_scans && Storage::binary_reads);
 Storage::reset_counts();assert(validate());assert(!Storage::directory_scans && !Storage::binary_reads);
 // Interrupted install must not fallback to a committed receipt or old seal.
 {detail::PackageMutationScope mutation(cp);assert(Storage::fs_write_text((cached/".brookesia-install.pending").string(),"{}",0));}
 reboot();Storage::reset_counts();auto pending=validate();assert(!pending && pending.error()=="package_transaction_pending");assert(!Storage::directory_scans && !Storage::binary_reads);
 {detail::PackageMutationScope mutation(cp);assert(Storage::fs_remove((cached/".brookesia-install.pending").string(),0));}
 assert(validate());
 // Failure durably removing a record blocks the content write itself.
 fs::create_directories(temporary/"child");
 {detail::PackageMutationScope mutation(cp);auto changed=Storage::fs_write_text(code.string(),"bad",0);assert(!changed);}
 assert(*Storage::fs_read_text(code.string(),0)==source && !is_runtime_package_validation_current(cached.string(),cp));
 fs::remove_all(temporary);assert(validate());
 // Corruption/tampering of authenticated claims causes full revalidation.
 auto record=boost::json::parse(*Storage::fs_read_text(seal.string(),0)).as_object();record["unsigned"]=false;
 std::ofstream(seal)<<boost::json::serialize(record);
 reboot();Storage::reset_counts();assert(validate());assert(Storage::directory_scans && Storage::binary_reads);
 cp.platform_baseline="new-rules";assert(!validate());assert(!is_runtime_package_validation_current(cached.string(),cp));
 cp.platform_baseline=p.platform_baseline;assert(validate());
 Storage::reset_counts();assert(validate());assert(!Storage::directory_scans && !Storage::binary_reads);
 // A different system cannot reuse the in-memory compatibility admission.
 Storage::reset_counts();assert(validate_installed_runtime_package(cached.string(),"other",cp));assert(Storage::directory_scans && Storage::binary_reads);
 // Trust-key changes invalidate the binding even when package bytes are intact.
 cp.public_key_pem_path=(root/"release-key.pem").string();
 {detail::PackageMutationScope mutation(cp);assert(Storage::fs_write_text(cp.public_key_pem_path,"key-v1",0));}
 assert(validate());
 {detail::PackageMutationScope mutation(cp);assert(Storage::fs_write_text(cp.public_key_pem_path,"key-v2",0));}
 Storage::reset_counts();assert(validate());assert(Storage::directory_scans && Storage::binary_reads);
 // An ancestor mutation invalidates seals of undiscovered apps after reboot.
 reboot();assert(fs::exists(seal));
 {detail::PackageMutationScope mutation(cp);assert(Storage::fs_mkdir(cache_root.string(),0));}
 assert(!fs::exists(seal));Storage::reset_counts();assert(validate());assert(Storage::directory_scans && Storage::binary_reads);
 // The actual transaction path still commits, updates, and rolls back with the
 // protection callback enabled; committed versions are immediately reusable.
 System protected_system;protected_system.root=cache_root;protected_system.impl_->package_policy_=cp;
 PackageInstallOptions options;options.developer_confirmed=true;
 auto installed=protected_system.install_runtime_app_package((root/"update.bpk").string(),options);
 assert(installed);
 Storage::reset_counts();auto v=validate();assert(v && v->manifest.version=="2.0.0");assert(!Storage::directory_scans && !Storage::binary_reads);
 protected_system.fail_install_version="3.0.0";assert(!protected_system.install_runtime_app_package((root/"update2.bpk").string(),options));
 assert(validate()->manifest.version=="2.0.0" && fs::exists(cached/"data/private"));
 reboot();Storage::reset_counts();assert(validate());assert(!Storage::directory_scans && !Storage::binary_reads);
 esp_brookesia::service::storage_guard={};esp_brookesia::service::kv_guard={};
}
'''

HARNESS = r'''
#include <cassert>
#include <iostream>
#include <boost/json/src.hpp>
#include "mbedtls/md.h"
#include "brookesia/system_core/package.hpp"
#include "brookesia/service_helper/system/storage.hpp"
#include <cstdlib>
#include <new>
bool fail_package_member_allocation = false;
void *operator new(size_t size) {
 if (fail_package_member_allocation && size == 323664) throw std::bad_alloc();
 if (auto *pointer = std::malloc(size ? size : 1)) return pointer;
 throw std::bad_alloc();
}
void operator delete(void *pointer) noexcept { std::free(pointer); }
void operator delete(void *pointer, size_t) noexcept { std::free(pointer); }
namespace esp_brookesia::system::core {
std::expected<void,std::string> verify_app_package_release_bytes(const std::vector<uint8_t>&,const AppPackageReleaseVerifyOptions&) {return std::unexpected("injected invalid signature");}
}
int main(int argc,char**argv){
 using namespace esp_brookesia::system::core;
 using Storage=esp_brookesia::service::helper::Storage;
 namespace fs=std::filesystem;
 fs::path root=argv[1];bool developer=true;
 RuntimePackagePolicy p{.enforce=true,.developer_enabled=[&]{return developer;},.platform_baseline="test"};
 auto inspect=[&](const char*n){return inspect_runtime_package((root/n).string(),"espocket",p);};
 fail_package_member_allocation = true;
 auto exhausted = inspect("large-seed.bpk");
 assert(!exhausted && exhausted.error() == "Package OOM");
 fail_package_member_allocation = false;
 assert(inspect("large-seed.bpk"));
 {
  System slow_write;slow_write.root=root/"slow-write";slow_write.impl_->package_policy_=p;
  PackageInstallOptions options;options.developer_confirmed=true;
  Storage::write_wait_ms=9000;
  assert(slow_write.install_runtime_app_package((root/"large-seed.bpk").string(),options));
  Storage::write_wait_ms=30001;
  auto timed_out=slow_write.install_runtime_app_package((root/"large-seed.bpk").string(),options);
  assert(!timed_out && timed_out.error()=="injected write timeout");
  Storage::write_wait_ms=0;
  assert(validate_installed_runtime_package((slow_write.root/"test.game").string(),"espocket",p));
 }
 auto app=inspect("super.bpk");assert(app && app->unsigned_exception && app->super_exception);
 assert(inspect("espocket.bpk") && !inspect("espocket.bpk")->super_exception);
 assert(!inspect("other.bpk"));
 developer=false;assert(!inspect("super.bpk"));assert(!inspect("espocket.bpk"));developer=true;
 assert(inspect("seeds.bpk"));
 {
  System seeded;seeded.root=root/"seeded";seeded.impl_->package_policy_=p;
  PackageInstallOptions options;options.developer_confirmed=true;
  auto installed_seed=seeded.install_runtime_app_package((root/"seeds.bpk").string(),options);
  assert(installed_seed);
  const auto path=seeded.root/"test.game";
  assert(*Storage::fs_read_text((path/"data/config.pem.example").string(),0)=="default");
  assert(*Storage::fs_read_text((path/"files/music/0.mp3").string(),0)=="audio");
  assert(Storage::fs_write_text((path/"data/config.json").string(),"user config",0));
  assert(Storage::fs_write_text((path/"files/music/0.mp3").string(),"user audio",0));
  assert(validate_installed_runtime_package(path.string(),"espocket",p));
  options.replace_existing=true;
  assert(seeded.install_runtime_app_package((root/"seeds-update.bpk").string(),options));
  assert(*Storage::fs_read_text((path/"data/config.json").string(),0)=="user config");
  assert(*Storage::fs_read_text((path/"files/music/0.mp3").string(),0)=="user audio");
  assert(*Storage::fs_read_text((path/"data/new.json").string(),0)=="new default");
  assert(*Storage::fs_read_text((path/"files/music/new.mp3").string(),0)=="new audio");
  assert(validate_installed_runtime_package(path.string(),"espocket",p));
  std::ofstream(path/"res/root.json")<<"tampered";
  assert(!validate_installed_runtime_package(path.string(),"espocket",p));
 }
 for(const auto n:{"half.bpk","signed.bpk","traversal.bpk","duplicate.bpk","case.bpk","reserved.bpk","private-case.bpk","private-root.bpk","private-entry.bpk","private-resource.bpk","corrupt.bpk","header.bpk"}){
  if(inspect(n)){std::cerr<<"unexpected admission "<<n;return 1;}}
 p.public_key_pem_path="inert.pem";assert(!inspect("signed.bpk"));
 assert(!inspect_runtime_package((root/"super.bpk").string(),"espocket",p,std::string(64,'0')));
 assert(app->artifact_sha256==argv[2]);
 auto staged=unpack_app_package_to((root/"super.bpk").string(),(root/"apps").string(),"super",app->artifact_sha256);assert(staged);
 assert(!unpack_app_package_to((root/"super.bpk").string(),(root/"bad").string(),"super",std::string(64,'0')));
 const auto final=root/"apps"/app->manifest.id;
 fs::copy_file(root/"super.bpk",final/".brookesia-package.bpk");
 assert(write_runtime_package_receipt(final.string(),*app,p));
 assert(!validate_installed_runtime_package(final.string(),"espocket",p));
 assert(validate_installed_runtime_package(final.string(),"espocket",p,true,true));
 assert(commit_runtime_package_receipt(final.string()));
 assert(validate_installed_runtime_package(final.string(),"espocket",p));
 developer=false;assert(!validate_installed_runtime_package(final.string(),"espocket",p));
 assert(validate_installed_runtime_package(final.string(),"espocket",p,false));developer=true;
 auto original=*Storage::fs_read_text((final/"app/app.js").string(),0);
 std::ofstream(final/"app/app.js")<<"tampered";assert(!validate_installed_runtime_package(final.string(),"espocket",p));
 std::ofstream(final/"app/app.js")<<original;
 std::ofstream(final/"extra")<<"x";assert(!validate_installed_runtime_package(final.string(),"espocket",p));fs::remove(final/"extra");
 auto receipt=*Storage::fs_read_text((final/".brookesia-install.json").string(),0);
 auto receipt_json=boost::json::parse(receipt).as_object();
 assert(receipt_json.at("manifest").as_string().size()==64);
 assert(receipt_json.at("signing_key").as_string()=="unverified");
 assert(!receipt_json.at("transaction").as_string().empty());
 receipt_json["unsigned"]=false;
 std::ofstream(final/".brookesia-install.json")<<boost::json::serialize(receipt_json);
 assert(!validate_installed_runtime_package(final.string(),"espocket",p));
 std::ofstream(final/".brookesia-install.json")<<receipt;
 fs::create_directories(final/"data");std::ofstream(final/"data/private")<<"preserve me";
 assert(validate_installed_runtime_package(final.string(),"espocket",p));
 const auto backup=root/"apps/.rollback"/app->manifest.id;fs::create_directories(backup.parent_path());fs::rename(final,backup);
 // Power loss after moving old version; recover it before discovery.
 assert(recover_runtime_package_updates((root/"apps").string(),"espocket",p));
 assert(fs::exists(final/"data/private") && !fs::exists(backup));
 fs::rename(final,backup);fs::create_directories(final);std::ofstream(final/"manifest.json")<<"{}";
 Storage::fail_rename_to=final.string();assert(!recover_runtime_package_updates((root/"apps").string(),"espocket",p));assert(fs::exists(backup/"data/private"));
 Storage::fail_rename_to.clear();assert(recover_runtime_package_updates((root/"apps").string(),"espocket",p));
 // A committed new version survives reboot; obsolete backup is cleaned only after validation.
 fs::copy(final,backup,fs::copy_options::recursive);assert(recover_runtime_package_updates((root/"apps").string(),"espocket",p));assert(!fs::exists(backup));
 // A promoted first install with only a pending receipt and orphan staging are removed.
 const auto interrupted=root/"first-install";fs::create_directories(interrupted/".rollback");fs::create_directories(interrupted/"orphan.app");
 std::ofstream(interrupted/"orphan.app/.brookesia-install.pending")<<"{}";
 fs::create_directories(interrupted/".installing/candidate");
 assert(recover_runtime_package_updates(interrupted.string(),"espocket",p));
 assert(!fs::exists(interrupted/"orphan.app") && !fs::exists(interrupted/".installing"));
 // Explicit built-in allowlist uses exact members and does not grant all same-ID content.
 const auto builtin=root/"builtin";fs::copy(final,builtin,fs::copy_options::recursive);
 fs::remove(builtin/".brookesia-package.bpk");fs::remove(builtin/".brookesia-install.json");
 assert(!validate_installed_runtime_package(builtin.string(),"super",p));p.built_in_members[app->manifest.id]=app->members;
 assert(validate_installed_runtime_package(builtin.string(),"super",p));
 std::ofstream(builtin/"app/app.js")<<"changed";assert(!validate_installed_runtime_package(builtin.string(),"super",p));
}
'''


class RuntimePackageAdmissionTest(unittest.TestCase):
    def test_actual_core_package_gate_and_recovery(self):
        sys.path.insert(0, str(ROOT / 'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='espocket-package-gate-') as directory:
            root = Path(directory)
            core = prepare(CORE, ROOT/'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json', root/'core')
            stubs = root/'stubs'
            def write(name, text):
                path=stubs/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
            write('brookesia/system_core/app/types.hpp', TYPES)
            write('brookesia/runtime_manager/types.hpp', '#pragma once\n#include "brookesia/system_core/app/types.hpp"\n')
            write('brookesia/system_core/macro_configs.h', '#pragma once\n#define BROOKESIA_SYSTEM_CORE_SYSTEM_ENABLE_DEBUG_LOG 0\n')
            write('private/utils.hpp', '#pragma once\n#define BROOKESIA_LOG_TRACE_GUARD(...)\n#define BROOKESIA_LOGD(...)\n#define BROOKESIA_LOGW(...)\n#define BROOKESIA_LOGI(...)\n')
            write('private/app/service_requirement.hpp', '#pragma once\nnamespace esp_brookesia::system::core::detail { inline std::expected<int,std::string> parse_service_version(const std::string&s){return s.empty()?std::expected<int,std::string>(std::unexpected("empty")):0;} }\n')
            write('brookesia/service_manager/common.hpp', CALL_CONTEXT)
            write('brookesia/service_storage.hpp', STORAGE_GUARD)
            write('brookesia/service_helper/system/storage.hpp', STORAGE)
            if sys.platform == 'darwin':
                crypto = '#include <CommonCrypto/CommonDigest.h>\n#include <CommonCrypto/CommonHMAC.h>\ninline int host_hmac(const unsigned char*k,size_t kl,const unsigned char*p,size_t n,unsigned char*out){CCHmac(kCCHmacAlgSHA256,k,kl,p,n,out);return 0;}\ninline int host_sha256(const unsigned char*p,size_t n,unsigned char*out){return CC_SHA256(p,n,out)?0:-1;}\n'
                crypto_flags=[]
            else:
                crypto = '#include <openssl/sha.h>\n#include <openssl/hmac.h>\ninline int host_hmac(const unsigned char*k,size_t kl,const unsigned char*p,size_t n,unsigned char*out){return HMAC(EVP_sha256(),k,kl,p,n,out,nullptr)?0:-1;}\ninline int host_sha256(const unsigned char*p,size_t n,unsigned char*out){return SHA256(p,n,out)?0:-1;}\n'
                crypto_flags=['-lcrypto']
            write('mbedtls/md.h', '#pragma once\n'+crypto+'\ninline constexpr int MBEDTLS_MD_SHA256=1;\ninline const int*mbedtls_md_info_from_type(int){return &MBEDTLS_MD_SHA256;}\ninline int mbedtls_md(const int*,const unsigned char*p,size_t n,unsigned char*out){return host_sha256(p,n,out); }\ninline int mbedtls_md_hmac(const int*,const unsigned char*k,size_t kl,const unsigned char*p,size_t n,unsigned char*out){return host_hmac(k,kl,p,n,out);}\n')
            write('esp_random.h', '#pragma once\n#include <random>\ninline void esp_fill_random(void*p,size_t n){std::random_device r;auto bytes=static_cast<unsigned char*>(p);while(n--)*bytes++=static_cast<unsigned char>(r());}\n')
            fixtures=root/'fixtures';fixtures.mkdir()
            def package(name, systems=None, extra=(), version='1.0.0', entry='app/app.js', resource_dir='res'):
                manifest={'package':{'id':'test.game','version':version,'systems':systems or ['super']},'runtime':{'type':'JavaScript','entry':'app/app.js','resource_dir':'res'}}
                manifest['runtime'].update(entry=entry, resource_dir=resource_dir)
                with zipfile.ZipFile(fixtures/name,'w',zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr('manifest.json',json.dumps(manifest));archive.writestr('app/app.js','export function on_start() {}')
                    archive.writestr('res/profile.json',json.dumps({'root':'root.json','screen_flows':[{'screen_flow':'main','layer':'AppDefault'}]}))
                    archive.writestr('res/root.json','{}')
                    for member,value in extra:archive.writestr(member,value)
            package('super.bpk');package('update.bpk',version='2.0.0');package('update2.bpk',version='3.0.0');package('espocket.bpk',['espocket']);package('other.bpk',['other'])
            package('half.bpk',extra=[('META-INF/hash.json','{}')])
            package('signed.bpk',extra=[('META-INF/hash.json','{}'),('META-INF/signature.sig','invalid')])
            seeds=[('data/config.pem.example','default'),('data/config.json','defaults'),('files/music/0.mp3','audio')]
            package('seeds.bpk',extra=seeds)
            package('large-seed.bpk',extra=[('files/music/0.mp3', b'a' * 323664)])
            package('seeds-update.bpk',extra=seeds+[('data/new.json','new default'),('files/music/new.mp3','new audio')],version='2.0.0')
            package('private-entry.bpk',extra=[('data/code.js','code')],entry='data/code.js')
            package('private-resource.bpk',resource_dir='files')
            for name,member in [('traversal.bpk','res/../escape'),('duplicate.bpk','app/app.js'),('case.bpk','APP/APP.JS'),('reserved.bpk','.brookesia-verified.json'),('private-case.bpk','Data/file'),('private-root.bpk','data')]:package(name,extra=[(member,'bad')])
            for name,offset in [('corrupt.bpk',16),('header.bpk',30)]:
                data=bytearray((fixtures/'super.bpk').read_bytes())
                if name=='corrupt.bpk':
                    offset=data.index(b'PK\x01\x02')+16
                data[offset]^=1;(fixtures/name).write_bytes(data)
            methods=(core/'src/app/app.cpp').read_text()
            helpers=methods[methods.index('std::expected<void, std::string> remove_path_tree_if_exists('):methods.index('std::expected<std::filesystem::path, std::string> get_default_install_app_root(')]
            transaction=methods[methods.index('std::expected<AppId, std::string> System::install_runtime_app_package('):methods.index('std::expected<void, std::string> System::write_runtime_app_member(')]
            prefix='#include \"private/app/package_validation.hpp\"\n#include <optional>\n#include <chrono>\n#include "private/utils.hpp"\n#include "brookesia/system_core/package.hpp"\n#include "brookesia/service_helper/system/storage.hpp"\n'
            prefix += '#include "private/filesystem.hpp"\n'
            removal=''
            combined=prefix+TRANSACTION_ADAPTER+removal+helpers+transaction+'}\n'+HARNESS
            combined=combined.replace(' // Explicit built-in allowlist',TRANSACTION_MATRIX+CACHE_MATRIX+'\n // Explicit built-in allowlist')
            harness=root/'harness.cpp';harness.write_text(combined)
            binary=root/'gate'
            command=[os.environ.get('CXX','clang++'),'-std=c++23','-DESP_PLATFORM','-DBOOST_NO_USER_CONFIG','-I'+str(stubs),'-I'+str(core/'include'),'-I'+str(core/'src'),'-I'+str(ROOT/'firmware/managed_components/espressif__esp-boost/src'),str(core/'src/app/package.cpp'),str(core/'src/app/package_validation.cpp'),str(harness),'-lz',*crypto_flags,'-o',str(binary)]
            compiled=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr[-12000:])
            result=subprocess.run([str(binary),str(fixtures),hashlib.sha256((fixtures/'super.bpk').read_bytes()).hexdigest()],capture_output=True,text=True)
            if result.returncode:
                import re
                location=re.search(r'harness.cpp, line (\d+)',result.stderr)
                if location:
                    line=int(location.group(1))
                    result.stderr+='\n'+ '\n'.join(combined.splitlines()[max(0,line-3):line+2])
            self.assertEqual(result.returncode,0,result.stderr)
