"""Run the actual Core GUI dispatch methods against a fake GUI/scheduler boundary."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class CoreNativeContentTest(unittest.TestCase):
    def test_native_document_and_foreground_admission(self):
        with tempfile.TemporaryDirectory(prefix='core-native-content-') as directory:
            work = Path(directory)
            component = 'espressif__brookesia_system_core'
            core = prepare(ROOT / 'firmware/managed_components' / component,
                           ROOT / 'firmware/patches' / component / '0.8.4/manifest.json', work / 'core')
            text = (core / 'src/system/gui.cpp').read_text()
            begin = text.index('std::expected<gui::NativeContentToken, std::string> System::gui_mount_native_content(')
            methods = text[begin:text.index('std::expected<void, std::string> System::gui_set_value(', begin)]
            source = work / 'test.cpp'
            source.write_text(r'''
#include <cassert>
#include <expected>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
using AppId=int;constexpr int SYSTEM_GUI_TASK_GROUP=1;
enum class AppKind{Native,Runtime};enum class AppState{Running,Paused,Stopping,Installed,Stopped,Error};
namespace gui {
using DocumentId=int;struct NativeContent{};struct NativeContentToken{};struct NativePointerFrame{};
using NativeContentCallback=std::function<void(NativeContent&)>;
struct Runtime {
 int calls=0,doc=0;std::optional<uint64_t> epoch;
 std::expected<NativeContentToken,std::string> mount_native_content(int d,std::string_view,std::shared_ptr<NativeContent>){doc=d;++calls;return NativeContentToken{};}
 std::expected<void,std::string> invoke_native_content(int d,NativeContentToken,NativeContentCallback){doc=d;++calls;return {};}
 bool unmount_native_content(int d,NativeContentToken){doc=d;++calls;return true;}
 std::expected<NativePointerFrame,std::string> read_native_pointer_frame(int d,NativeContentToken,std::optional<uint64_t> e){doc=d;epoch=e;++calls;return NativePointerFrame{};}
};
}
struct Record {struct Info{struct Manifest{AppKind kind=AppKind::Native;}manifest;AppState state=AppState::Running;}info;std::optional<int> document_id=41;};
struct Impl {
 Record record;gui::Runtime gui;gui::Runtime* gui_runtime_=&gui;int active_app_id_=7;bool missing=false,reject=false;int flushes=0;
 struct Config{std::function<std::optional<uint64_t>(AppId)> native_pointer_access;}config_;
 std::expected<Record*,std::string> get_record(int){if(missing)return std::unexpected("missing");return &record;}
 void flush_pending_gui_bindings(int){++flushes;}
 template<class R,class F>R run_task_sync(int,F f,R fail){return reject?fail:f();}
};
struct System {
 Impl backing;Impl* impl_=&backing;
 std::expected<gui::NativeContentToken,std::string> gui_mount_native_content(AppId,std::string_view,std::shared_ptr<gui::NativeContent>);
 std::expected<void,std::string> gui_invoke_native_content(AppId,const gui::NativeContentToken&,const gui::NativeContentCallback&);
 bool gui_unmount_native_content(AppId,const gui::NativeContentToken&);
 std::expected<gui::NativePointerFrame,std::string> gui_read_native_pointer_frame(AppId,const gui::NativeContentToken&);
};
''' + methods + r'''
int main(){
 System s;gui::NativeContentToken token;auto content=std::make_shared<gui::NativeContent>();
 auto& b=s.backing;
 assert(s.gui_mount_native_content(7,"/root/content",content));assert(b.gui.doc==41);
 assert(s.gui_invoke_native_content(7,token,{}));assert(s.gui_unmount_native_content(7,token));
 assert(s.gui_read_native_pointer_frame(7,token));assert(!b.gui.epoch); // fail closed without product arbiter
 b.config_.native_pointer_access=[](int id)->std::optional<uint64_t>{assert(id==7);return 3;};
 assert(s.gui_read_native_pointer_frame(7,token));assert(b.gui.epoch==3);
 b.record.info.state=AppState::Paused;assert(s.gui_read_native_pointer_frame(7,token));assert(!b.gui.epoch);
 b.record.info.state=AppState::Running;b.active_app_id_=8;assert(s.gui_read_native_pointer_frame(7,token));assert(!b.gui.epoch);
 b.active_app_id_=7;b.record.info.manifest.kind=AppKind::Runtime;
 int before=b.gui.calls;
 assert(!s.gui_mount_native_content(7,"/root/content",content));assert(!s.gui_invoke_native_content(7,token,{}));
 assert(!s.gui_unmount_native_content(7,token));assert(!s.gui_read_native_pointer_frame(7,token));assert(b.gui.calls==before);
 b.record.info.manifest.kind=AppKind::Native;b.record.document_id.reset();
 assert(!s.gui_mount_native_content(7,"/root/content",content));assert(!s.gui_read_native_pointer_frame(7,token));
 b.record.document_id=99;assert(s.gui_invoke_native_content(7,token,{}));assert(b.gui.doc==99); // Runtime rejects previous document's token
 for(auto state:{AppState::Installed,AppState::Stopped,AppState::Error}){
  b.record.info.state=state;assert(!s.gui_mount_native_content(7,"/root/content",content));assert(!s.gui_invoke_native_content(7,token,{}));
 }
 b.record.info.state=AppState::Running;
 b.reject=true;before=b.gui.calls;assert(!s.gui_mount_native_content(7,"/root/content",content));assert(b.gui.calls==before);
}
''')
            binary = work / 'test'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(source), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=10)

    def test_stopped_preloaded_document_revokes_native_mounts(self):
        with tempfile.TemporaryDirectory(prefix='core-retained-native-') as directory:
            work = Path(directory)
            component = 'espressif__brookesia_system_core'
            core = prepare(ROOT / 'firmware/managed_components' / component,
                           ROOT / 'firmware/patches' / component / '0.8.4/manifest.json', work / 'core')
            text = (core / 'src/system/gui.cpp').read_text()
            begin = text.index('void System::Impl::cleanup_stopped_app_gui(')
            method = text[begin:text.index('void System::Impl::rollback_installed_app_gui(', begin)]
            source = work / 'test.cpp'
            source.write_text(r'''
#include <cassert>
#include <optional>
#include <string>
#include <vector>
struct AppRecord {struct Info{int app_id=7;}info;bool preload_dom=true;std::optional<int> document_id=41;};
std::vector<std::string> calls;
struct Gui {void clear_native_content(int d){assert(d==41);calls.push_back("revoke");}};
struct System {struct Impl {
 Gui gui;Gui* gui_runtime_=&gui;
 void clear_pending_gui_bindings(int){calls.push_back("bindings");}
 void clear_pending_gui_image_sources(int){calls.push_back("images");}
 void release_app_gui_presentation(AppRecord&){calls.push_back("presentation");}
 void unload_gui(AppRecord&){calls.push_back("unload");}
 void unregister_app_gui_resources(AppRecord&){calls.push_back("resources");}
 void cleanup_stopped_app_gui(AppRecord&);
};};
''' + method + r'''
int main(){
 System::Impl owner;AppRecord record;
 owner.cleanup_stopped_app_gui(record);
 assert((calls==std::vector<std::string>{"bindings","images","revoke","presentation"}));
 assert(record.document_id==41);
 calls.clear();record.preload_dom=false;owner.cleanup_stopped_app_gui(record);
 assert((calls==std::vector<std::string>{"bindings","images","revoke","unload","resources"}));
 calls.clear();record.document_id.reset();record.preload_dom=true;owner.cleanup_stopped_app_gui(record);
 assert((calls==std::vector<std::string>{"bindings","images","presentation"}));
}
''')
            binary = work / 'test'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(source), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=10)
