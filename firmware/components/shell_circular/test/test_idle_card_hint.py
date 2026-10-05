"""The real Shell timer hint path must not wait on LVGL when no hint exists."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
OWNER = Path(__file__).resolve().parents[1]
class IdleCardHintTest(unittest.TestCase):
    def test_no_hint_has_no_gui_lock_but_creation_update_and_removal_still_lock(self):
        source=(OWNER/'src/shell_navigation.cpp').read_text();start=source.index('void CircularShell::sync_card_hint(');method=source[start:source.index('void CircularShell::sync_default_back(',start)]
        code=r'''
#include <cassert>
#include <memory>
#include <string>
unsigned locks=0,created=0,deleted=0,updates=0;int label;
struct LvglLock{LvglLock(){++locks;}operator bool()const{return true;}};
bool lv_obj_is_valid(void*p){return p==&label;}void lv_obj_delete(void*){++deleted;}
void*lv_layer_top(){return nullptr;}void*lv_label_create(void*){++created;return &label;}
void lv_obj_remove_flag(void*,int){}void lv_obj_set_style_text_color(void*,int,int){}void lv_obj_set_style_text_font(void*,const void*,int){}void lv_obj_align(void*,int,int,int){}
void lv_label_set_text(void*,const char*){++updates;}int lv_color_hex(int n){return n;}int theme_color(const char*){return 0;}int lv_font_montserrat_18;
#define LV_OBJ_FLAG_CLICKABLE 1
#define LV_ALIGN_BOTTOM_MID 1
namespace espocket {enum class ShellSurface{LeftAppCard,RightAppCard};struct CircularShell {
 struct Back {void*card_hint=nullptr;};std::unique_ptr<Back>back_overlay_state_=std::make_unique<Back>();
 void sync_card_hint(bool);ShellSurface current_surface(){return ShellSurface::LeftAppCard;}
};
'''+method+r'''
}
int main(){espocket::CircularShell shell;
 for(int i=0;i<200;++i)shell.sync_card_hint(false);
 assert(locks==0 && created==0 && updates==0);
 shell.sync_card_hint(true);assert(locks==1 && created==1 && updates==1);
 shell.sync_card_hint(false);assert(locks==2 && deleted==1 && !shell.back_overlay_state_->card_hint);
 shell.sync_card_hint(false);assert(locks==2);
}
'''
        with tempfile.TemporaryDirectory() as d:
            cpp=Path(d)/'hint.cpp';binary=Path(d)/'hint';cpp.write_text(code)
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23',str(cpp),'-o',str(binary)],check=True)
            result=subprocess.run([str(binary)],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
if __name__=='__main__':unittest.main()
