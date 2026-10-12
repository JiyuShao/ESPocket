"""Execute patched Runtime and LVGL native mount methods with fake LVGL resources.

The fake supplies allocation/locking/node lookup, not the lifecycle decisions under
 test. Real drawing, scheduler concurrency and hardware remain device acceptance.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


def section(path, start, end):
    text = path.read_text()
    begin = text.index(start)
    return text[begin:text.index(end, begin)]


class NativeContentTest(unittest.TestCase):
    def test_mount_failure_revocation_and_document_identity(self):
        with tempfile.TemporaryDirectory(prefix='espocket-native-content-') as directory:
            work = Path(directory)
            components = {}
            for name, version in [('gui_interface', '0.8.2'), ('gui_lvgl', '0.8.5')]:
                component = 'espressif__brookesia_' + name
                components[name] = prepare(
                    ROOT / 'firmware/managed_components' / component,
                    ROOT / 'firmware/patches' / component / version / 'manifest.json', work / name)
            interface, lvgl = components['gui_interface'], components['gui_lvgl']
            pointer = (interface / 'include/brookesia/gui_interface/native_pointer.hpp').read_text()
            pointer = pointer[pointer.index('namespace esp_brookesia::gui {'):]
            native = (interface / 'include/brookesia/gui_interface/native_content.hpp').read_text()
            native = native[native.index('namespace esp_brookesia::gui {'):]
            typed = (lvgl / 'include/brookesia/gui_lvgl/native_content.hpp').read_text()
            typed = typed[typed.index('namespace esp_brookesia::gui::lvgl {'):]
            backend_methods = section(lvgl / 'src/backend.cpp',
                                      'void BackendImpl::revoke_native_content(',
                                      'void BackendImpl::apply_props(')
            runtime_methods = section(interface / 'src/runtime.cpp',
                                      'std::expected<NativeContentToken, std::string> Runtime::mount_native_content(',
                                      'std::expected<void, std::string> Runtime::update(')
            harness = r'''
#include <cassert>
#include <algorithm>
#include <cstdint>
#include <expected>
#include <functional>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>
namespace esp_brookesia::gui {
struct DocumentId {
    uint64_t v=0; DocumentId()=default; explicit DocumentId(uint64_t n):v(n){}
    uint64_t value()const{return v;}
    bool operator==(const DocumentId&)const=default;
};
using BackendHandle=DocumentId;
enum class NodeType{Container,Label};
}
int lock_depth=0, live_roots=0; bool allocation_fails=false;
struct _lv_obj_t {bool live=true;}; using lv_obj_t=_lv_obj_t;
struct ThreadLockGuard{ThreadLockGuard(){++lock_depth;}~ThreadLockGuard(){--lock_depth;}};
lv_obj_t* lv_obj_create(lv_obj_t*){assert(lock_depth);if(allocation_fails)return nullptr;++live_roots;return new lv_obj_t;}
bool lv_obj_is_valid(lv_obj_t* o){return o && o->live;}
void lv_obj_delete(lv_obj_t* o){assert(lock_depth && o->live);o->live=false;--live_roots;delete o;}
void lv_obj_remove_style_all(lv_obj_t*){}
void lv_obj_set_size(lv_obj_t*,int,int){}
void lv_obj_remove_flag(lv_obj_t*,int){}
bool lv_obj_is_visible(lv_obj_t* o){return o && o->live;}
int lv_obj_get_display(lv_obj_t*){return 1;}
struct lv_area_t {int x1=10,y1=20,x2=110,y2=120;};
void lv_obj_get_coords(lv_obj_t*,lv_area_t* a){*a=lv_area_t{};}
#define LV_PCT(x) (x)
#define LV_OBJ_FLAG_SCROLLABLE 1
#define LV_OBJ_FLAG_OVERFLOW_VISIBLE 2
''' + pointer + native + typed + r'''
namespace esp_brookesia::gui::lvgl {
struct DisplaySource {
    NativePointerFrame frame;
    static DisplaySource& get_instance(){static DisplaySource s;return s;}
    NativePointerFrame cached_pointer_frame(){return frame;}
    int display(){return 1;}
};
struct Record {
    NodeType type=NodeType::Container; lv_obj_t* object=nullptr;
    struct NativeMount {uint64_t id=0;std::shared_ptr<lvgl::NativeContent> content;lv_obj_t* root=nullptr;NativePointerDelivery pointer_delivery;};
    std::unique_ptr<NativeMount> native_mount;
};
class BackendImpl {
public:
    std::map<uint64_t,Record> records; uint64_t next_native_mount_id_=1;
    Record* find_record(BackendHandle h){auto it=records.find(h.value());return it==records.end()?nullptr:&it->second;}
    void revoke_native_content(Record&);
    std::expected<uint64_t,std::string> mount_native_content(BackendHandle,std::shared_ptr<gui::NativeContent>);
    std::expected<void,std::string> invoke_native_content(BackendHandle,uint64_t,const NativeContentCallback&);
    bool unmount_native_content(BackendHandle,uint64_t);
    void clear_native_content(BackendHandle h){ThreadLockGuard lock;if(auto* record=find_record(h))revoke_native_content(*record);}
    std::expected<NativePointerFrame,std::string> read_native_pointer_frame(BackendHandle,uint64_t,std::optional<uint64_t>);
};
''' + backend_methods + r'''
}
namespace esp_brookesia::gui {
std::string normalize_absolute_path(std::string_view p){return std::string(p);}
struct Runtime {
    struct Node {NodeType type=NodeType::Container;};
    struct NodeRecord {BackendHandle handle;Node definition;const Node& node()const{return definition;}};
    struct Tree {std::map<uint64_t,NodeRecord> nodes;std::map<uint64_t,uint64_t> handle_to_uid;};
    struct Impl {
        std::map<uint64_t,Tree> trees;
        std::shared_ptr<const uint8_t> native_identity_=std::make_shared<const uint8_t>(0);
        std::shared_ptr<lvgl::BackendImpl> backend=std::make_shared<lvgl::BackendImpl>();
        std::expected<void,std::string> refresh_document_if_dirty(Runtime*,DocumentId){return {};}
        Tree* resolve_tree(DocumentId d){auto i=trees.find(d.value());return i==trees.end()?nullptr:&i->second;}
        std::optional<uint64_t> resolve_any_uid(Tree& t,std::string_view path){return path=="/root/content" && t.nodes.contains(1)?std::optional<uint64_t>(1):std::nullopt;}
        NodeRecord* find_node_record(Tree& t,uint64_t id){auto i=t.nodes.find(id);return i==t.nodes.end()?nullptr:&i->second;}
    };
    std::unique_ptr<Impl> impl_=std::make_unique<Impl>();
    std::expected<NativeContentToken,std::string> mount_native_content(DocumentId,std::string_view,std::shared_ptr<NativeContent>);
    std::expected<void,std::string> invoke_native_content(DocumentId,const NativeContentToken&,const NativeContentCallback&);
    bool unmount_native_content(DocumentId,const NativeContentToken&);
    void clear_native_content(DocumentId);
    std::expected<NativePointerFrame,std::string> read_native_pointer_frame(DocumentId,const NativeContentToken&,std::optional<uint64_t>);
};
''' + runtime_methods + r'''
}
using namespace esp_brookesia;
struct Content:gui::lvgl::NativeContent {
    int attaches=0,detaches=0;bool fail=false,throwing=false;lv_obj_t* root=nullptr;
    std::expected<void,std::string> attach(lv_obj_t* p)override{
        assert(lock_depth);root=p;++attaches;
        if(throwing)throw std::runtime_error("attach exception");
        if(fail)return std::unexpected("attach failure");return {};
    }
    void detach()noexcept override{assert(lock_depth && root && root->live);++detaches;root=nullptr;}
};
void add(gui::Runtime& r,uint64_t doc,uint64_t handle,lv_obj_t* parent){
    auto& t=r.impl_->trees[doc];t.nodes[1].handle=gui::BackendHandle(handle);t.handle_to_uid[handle]=1;
    r.impl_->backend->records[handle].object=parent;
}
int main(){
    lv_obj_t parent;gui::Runtime r;gui::DocumentId doc(1),other(2);add(r,1,10,&parent);add(r,2,20,&parent);
    auto c=std::make_shared<Content>();
    assert(!r.mount_native_content(doc,"/missing",c));assert(!r.mount_native_content(doc,"/root/content",nullptr));
    allocation_fails=true;assert(!r.mount_native_content(doc,"/root/content",c));assert(c->attaches==0 && live_roots==0);allocation_fails=false;
    c->fail=true;assert(!r.mount_native_content(doc,"/root/content",c));assert(c->detaches==1 && live_roots==0);
    c->fail=false;c->throwing=true;assert(!r.mount_native_content(doc,"/root/content",c));assert(c->detaches==2 && live_roots==0);c->throwing=false;
    auto first=r.mount_native_content(doc,"/root/content",c);assert(first && live_roots==1);
    assert(!r.mount_native_content(doc,"/root/content",std::make_shared<Content>()));
    assert(!r.mount_native_content(other,"/root/content",c));
    int calls=0;auto callback=[&](gui::NativeContent& actual){assert(lock_depth && &actual==c.get());++calls;};
    assert(r.invoke_native_content(doc,*first,callback));assert(calls==1);
    auto& frame=gui::lvgl::DisplaySource::get_instance().frame;
    frame.valid=true;frame.sequence=1;frame.points={{20,30,1},{200,20,2}};
    assert(r.read_native_pointer_frame(doc,*first,3)->cancelled);
    frame.sequence=2;frame.points.clear();assert(!r.read_native_pointer_frame(doc,*first,3)->cancelled);
    frame.sequence=3;frame.points={{20,30,1},{200,20,2}};
    auto clipped=r.read_native_pointer_frame(doc,*first,3);assert(clipped && clipped->points.size()==1);
    assert(clipped->points[0].x==10 && clipped->points[0].y==10);
    assert(!r.read_native_pointer_frame(other,*first,3));
    assert(r.read_native_pointer_frame(doc,*first,std::nullopt)->points.empty());
    assert(!r.invoke_native_content(other,*first,callback));assert(!r.unmount_native_content(other,*first));
    gui::Runtime second;add(second,1,10,&parent);assert(!second.invoke_native_content(doc,*first,callback));
    assert(!second.mount_native_content(doc,"/root/content",c));
    assert(!r.invoke_native_content(doc,*first,{}));
    assert(!r.invoke_native_content(doc,*first,[](auto&){throw std::runtime_error("callback");}));
    assert(r.unmount_native_content(doc,*first));assert(!r.unmount_native_content(doc,*first));assert(live_roots==0);
    auto next=r.mount_native_content(doc,"/root/content",c);assert(next);
    assert(!r.invoke_native_content(doc,*first,callback));assert(!r.unmount_native_content(doc,*first));
    r.clear_native_content(doc);
    r.clear_native_content(doc); // stopped preloaded document: repeat is harmless
    assert(r.impl_->trees.contains(1)); // document itself stays resident
    assert(!r.invoke_native_content(doc,*next,callback));assert(live_roots==0);
    // Replace the node at the same path. Old identity must not select the new mount.
    r.impl_->trees[1].handle_to_uid.clear();r.impl_->backend->records.erase(10);add(r,1,30,&parent);
    auto replaced=r.mount_native_content(doc,"/root/content",c);assert(replaced);
    assert(!r.invoke_native_content(doc,*next,callback));
    {ThreadLockGuard lock;r.impl_->backend->revoke_native_content(r.impl_->backend->records.at(30));}
    r.impl_->trees.erase(1);assert(!r.invoke_native_content(doc,*replaced,callback));assert(calls==1 && live_roots==0);
}
'''
            harness = harness.replace('#include <map>', '#include <map>\n#include <optional>')
            source = work / 'probe.cpp'
            binary = work / 'probe'
            source.write_text(harness)
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(source), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], timeout=10, check=True)
            destroy = section(lvgl / 'src/backend.cpp', 'void BackendImpl::destroy_node(', 'void BackendImpl::revoke_native_content(')
            self.assertLess(destroy.index('revoke_native_content(record_it->second)'), destroy.index('lv_obj_delete(it->second.object)'))
