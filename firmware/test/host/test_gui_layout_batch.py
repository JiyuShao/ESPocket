"""Exercise the real backend GUI guard and relative-layout refresh orchestration."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


def exercise(component, directory):
    backend = (component / 'src/backend.cpp').read_text()
    start = backend.index('std::optional<IBackend::ThreadGuard> BackendImpl::get_thread_guard() const')
    guard = backend[start:backend.index('BackendHandle BackendImpl::create_node(', start)]
    if 'void BackendImpl::flush_relative_layout()' not in guard:
        guard += '\nvoid BackendImpl::flush_relative_layout()const{}\n'
    start = backend.index('void BackendImpl::apply_layout(')
    apply = backend[start:backend.index('void BackendImpl::apply_placement(', start)]
    start = backend.index('std::optional<ViewFrame> BackendImpl::get_node_frame(')
    frame = backend[start:backend.index('bool BackendImpl::scroll_node_to_visible(', start)]
    layout = (component / 'src/layout.cpp').read_text()
    start = layout.index('void refresh_relative_placements(')
    refresh = layout[start:layout.index('\n} // namespace', start)]
    code = r'''
#include <cassert>
#include <functional>
#include <map>
#include <optional>
#include <string>
#include <stdexcept>
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS()
#define BROOKESIA_LOG_TRACE_GUARD()
#define BROOKESIA_LOGD(...)
int locks=0, scans=0, layouts=0;
void lock_thread(){++locks;}
void unlock_thread(){--locks;}
struct ThreadLockGuard{ThreadLockGuard(){lock_thread();}~ThreadLockGuard(){unlock_thread();}};
namespace lib_utils{struct FunctionGuard{std::function<void()>callback;FunctionGuard(std::function<void()>value):callback(value){}~FunctionGuard(){callback();}};}
struct IBackend{struct ThreadGuard{std::function<void()>lock,unlock;};};
enum class PlacementMode{Absolute,Relative};
struct Placement{PlacementMode mode=PlacementMode::Absolute;std::string relative_to;};
struct Object{int x=0;};
bool lv_obj_is_valid(Object*object){return object!=nullptr;}
void lv_obj_update_layout(Object*){}
int lv_obj_get_x(Object*object){return object->x;}
int lv_obj_get_y(Object*){return 0;}
int lv_obj_get_width(Object*){return 10;}
int lv_obj_get_height(Object*){return 20;}
struct ViewFrame{int x,y,width,height;};
struct Record{Object* object;Placement placement;};
struct BackendHandle{int value;};
struct Layout{int x;};
enum class LayoutApplyMask{All};
struct BackendImpl{
 mutable unsigned layout_batch_depth=0;
 mutable bool relative_layout_dirty=false;
 std::map<int,Record>records;
 std::optional<IBackend::ThreadGuard>get_thread_guard()const;
 void request_relative_layout();
 void flush_relative_layout()const;
 void apply_layout(BackendHandle,const Layout&,LayoutApplyMask);
 std::optional<ViewFrame>get_node_frame(BackendHandle)const;
 Record*find_record(BackendHandle handle){auto found=records.find(handle.value);return found==records.end()?nullptr:&found->second;}
 const Record*find_record(BackendHandle handle)const{auto found=records.find(handle.value);return found==records.end()?nullptr:&found->second;}
};
const Placement&get_record_placement(const Record&record){++scans;return record.placement;}
void update_known_layer_layouts(BackendImpl&){++layouts;}
bool align_relative_record(BackendImpl&impl,Record&record,bool){
 if(record.placement.mode!=PlacementMode::Relative)return false;
 record.object->x=impl.records.at(std::stoi(record.placement.relative_to)).object->x+7;return true;
}
namespace lvgl{
void refresh_relative_placements(BackendImpl&);
void apply_layout(Record&record,const Layout&layout,LayoutApplyMask){record.object->x=layout.x;}
}
''' + guard + apply + frame + '\nnamespace lvgl{\n' + refresh + r'''
}
int main(){
 BackendImpl backend;Object anchor,relative;
 backend.records.emplace(1,Record{&anchor,{}});
 backend.records.emplace(2,Record{&relative,{PlacementMode::Relative,"1"}});
 auto guard=backend.get_thread_guard().value();
 guard.lock();guard.lock();
 for(int node=0;node<3000;++node)backend.apply_layout({1},{node},LayoutApplyMask::All);
 assert(layouts==0 && scans==0 && locks==2);
 guard.unlock();assert(layouts==0 && locks==1);
 guard.unlock();assert(layouts==2 && relative.x==3006 && scans<=2 && locks==0);
 backend.apply_layout({1},{42},LayoutApplyMask::All);
 assert(layouts==4 && relative.x==49 && locks==0);
 guard.lock();backend.apply_layout({1},{100},LayoutApplyMask::All);
 assert(backend.get_node_frame({2})->x==107);
 assert(layouts==6 && relative.x==107);
 backend.apply_layout({1},{200},LayoutApplyMask::All);guard.unlock();
 assert(layouts==8 && relative.x==207);
 guard.lock();backend.apply_layout({99},{0},LayoutApplyMask::All);guard.unlock();assert(layouts==8);
 guard.lock();backend.apply_layout({1},{500},LayoutApplyMask::All);
 backend.records.erase(2);guard.unlock();assert(layouts==8 && locks==0);
 guard.lock();try{backend.apply_layout({1},{600},LayoutApplyMask::All);throw std::runtime_error("abort");}
 catch(...){guard.unlock();}assert(locks==0 && backend.layout_batch_depth==0);
}
'''
    source = directory / 'batch.cpp'
    source.write_text(code)
    binary = directory / 'batch'
    subprocess.run(['c++', '-std=c++20', str(source), '-o', str(binary)], check=True)
    return subprocess.run([str(binary)], capture_output=True)


class GuiLayoutBatchTest(unittest.TestCase):
    def test_gui_owner_batches_refresh_and_keeps_relative_targets_current(self):
        with tempfile.TemporaryDirectory(prefix='gui-layout-batch-') as name:
            directory = Path(name)
            component = 'espressif__brookesia_gui_lvgl'
            patched = prepare(ROOT / 'firmware/managed_components' / component,
                              ROOT / 'firmware/patches' / component / '0.8.5/manifest.json', directory / 'patched')
            self.assertEqual(exercise(patched, directory).returncode, 0)


if __name__ == '__main__':
    unittest.main()
