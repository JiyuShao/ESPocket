"""Exercise the locked backend call that currently rebuilds relative layout for scroll offsets."""
import os
from pathlib import Path
import subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/firmware'))
from prepare_patched_component import prepare
SOURCE=ROOT/'firmware/managed_components/espressif__brookesia_gui_lvgl'
MANIFEST=ROOT/'firmware/patches/espressif__brookesia_gui_lvgl/0.8.5/manifest.json'
def exercise(source,directory):
 text=(source/'src/backend.cpp').read_text();start=text.index('void BackendImpl::apply_props(');method=text[start:text.index('std::expected<void, std::string> BackendImpl::preload_image_resource',start)]
 code=r'''
#include <cstdint>
#include <cassert>
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS()
using BackendHandle=int;
struct Node{};
enum class PropsApplyMask:uint64_t {None=0, ImageOffsetX=1ULL<<9,ImageOffsetY=1ULL<<10,ImageSource=1ULL<<6,LabelText=1ULL<<5,All=~0ULL};
constexpr PropsApplyMask operator|(PropsApplyMask a,PropsApplyMask b){return static_cast<PropsApplyMask>(static_cast<uint64_t>(a)|static_cast<uint64_t>(b));}
struct ThreadLockGuard {};
struct Record{void*object=reinterpret_cast<void*>(1);};
struct BackendImpl{Record record;Record*find_record(int h){return h==1?&record:nullptr;}void apply_props(BackendHandle,const Node&,PropsApplyMask);};
unsigned applied=0,relative=0;
namespace lvgl {void apply_props(BackendImpl&,Record&,const Node&,PropsApplyMask){++applied;}void refresh_relative_placements(BackendImpl&){++relative;}}
'''+method+r'''
int main(){BackendImpl backend;Node node;
 backend.apply_props(1,node,PropsApplyMask::ImageOffsetX);backend.apply_props(1,node,PropsApplyMask::ImageOffsetY);backend.apply_props(1,node,PropsApplyMask::ImageOffsetX|PropsApplyMask::ImageOffsetY);
 assert(applied==3 && relative==0); // Scrolling image pixels does not move any relative layout anchor.
 backend.apply_props(1,node,PropsApplyMask::ImageOffsetX|PropsApplyMask::ImageSource);backend.apply_props(1,node,PropsApplyMask::LabelText);backend.apply_props(1,node,PropsApplyMask::All);
 assert(applied==6 && relative==3); // Source/auto-sized text/unknown changes keep layout semantics.
 backend.apply_props(99,node,PropsApplyMask::All);backend.record.object=nullptr;backend.apply_props(1,node,PropsApplyMask::All);
 assert(applied==6 && relative==3);
}
'''
 p=Path(directory);cpp=p/'relative.cpp';binary=p/'relative';cpp.write_text(code)
 subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23',str(cpp),'-o',str(binary)],check=True)
 return subprocess.run([str(binary)],capture_output=True).returncode
class GuiRelativeRefreshTest(unittest.TestCase):
 def test_pixel_scroll_skips_layout_but_geometry_updates_keep_it(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertNotEqual(exercise(SOURCE,d),0)
   patched=prepare(SOURCE,MANIFEST,Path(d)/'patched');self.assertEqual(exercise(patched,d),0)
if __name__=='__main__':unittest.main()
