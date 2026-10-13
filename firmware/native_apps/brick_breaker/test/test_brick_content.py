"""Run production rendering methods against a bounded LVGL boundary double."""
import unittest
from test_brick_breaker import ROOT, run


class BrickContentTest(unittest.TestCase):
    def test_geometry_changed_only_updates_detach_and_partial_attach(self):
        header = (ROOT / 'src/brick_content.hpp').read_text()
        header = header[header.index('namespace espocket {'):]
        methods = (ROOT / 'src/brick_content.cpp').read_text()
        methods = methods[methods.index('namespace espocket {'):]
        run(r'''
#include <cassert>
#include <cmath>
#include <expected>
#include <string>
#include <cstdarg>
#include <cstdio>
#include "espocket/brick_model.hpp"
struct lv_obj_t{int w=0,h=0,x=0,y=0,flags=0,border=0,start=0,end=0;std::string text;};
int allocations=0,fail_at=-1,mutations=0;lv_obj_t objects[256];
constexpr int LV_OBJ_FLAG_CLICKABLE=1,LV_OBJ_FLAG_SCROLLABLE=2,LV_OBJ_FLAG_HIDDEN=4,LV_OPA_COVER=255;
constexpr int LV_PART_MAIN=0,LV_BORDER_SIDE_FULL=15,LV_RADIUS_CIRCLE=32767,LV_ALIGN_CENTER=0;
lv_obj_t*lv_obj_create(lv_obj_t*){if(allocations==fail_at)return nullptr;assert(allocations<256);return &objects[allocations++];}
auto lv_arc_create(lv_obj_t*p){return lv_obj_create(p);}auto lv_label_create(lv_obj_t*p){return lv_obj_create(p);}
void lv_obj_remove_style_all(lv_obj_t*){}void lv_obj_remove_flag(lv_obj_t*o,int f){o->flags&=~f;++mutations;}
void lv_obj_add_flag(lv_obj_t*o,int f){o->flags|=f;++mutations;}
void lv_obj_set_size(lv_obj_t*o,int w,int h){o->w=w;o->h=h;++mutations;}
void lv_obj_set_pos(lv_obj_t*o,int x,int y){o->x=x;o->y=y;++mutations;}
void lv_obj_center(lv_obj_t*){}void lv_obj_align(lv_obj_t*,int,int,int){++mutations;}
void lv_arc_set_value(lv_obj_t*,int){}void lv_arc_set_bg_angles(lv_obj_t*o,int a,int b){o->start=a;o->end=b;++mutations;}
int lv_color_hex(uint32_t v){return v;}int lv_color_white(){return 0xffffff;}
void lv_obj_set_style_border_width(lv_obj_t*o,int w,int){o->border=w;++mutations;}
#define STYLE(fn) void fn(lv_obj_t*,int,int){++mutations;}
STYLE(lv_obj_set_style_bg_opa) STYLE(lv_obj_set_style_bg_color) STYLE(lv_obj_set_style_border_color)
STYLE(lv_obj_set_style_border_side) STYLE(lv_obj_set_style_border_opa) STYLE(lv_obj_set_style_radius)
STYLE(lv_obj_set_style_arc_width) STYLE(lv_obj_set_style_arc_color) STYLE(lv_obj_set_style_text_color)
void lv_label_set_text(lv_obj_t*o,const char*s){o->text=s;++mutations;}
void lv_label_set_text_fmt(lv_obj_t*o,const char*f,...){char b[128];va_list a;va_start(a,f);vsnprintf(b,sizeof b,f,a);va_end(a);o->text=b;++mutations;}
namespace esp_brookesia::gui::lvgl{struct NativeContent{virtual ~NativeContent()=default;virtual std::expected<void,std::string>attach(lv_obj_t*)=0;virtual void detach()noexcept=0;};}
''' + header + methods + r'''
int main(){
 using namespace espocket;lv_obj_t root;BrickContent content;brick::Model model;
 assert(content.attach(&root));const int baseline=mutations;content.paint(model);assert(mutations==baseline);
 // Board, 36 reusable brick slots, wall, paddle, two beads, ball and two labels.
 assert(allocations==44 && objects[0].w==466 && objects[37].w==420 && objects[37].start==150 && objects[37].end==30 && objects[38].w==444);
 auto&s=const_cast<brick::State&>(model.state());s.x+=3;content.paint(model);assert(mutations==baseline+1);
 s.bricks[0].hp=2;content.paint(model);assert(objects[1].border==3);
 s.bricks[0].hp=1;content.paint(model);assert(objects[1].border==0 && !(objects[1].flags&LV_OBJ_FLAG_HIDDEN));
 s.bricks[0].hp=0;--s.remaining;content.paint(model);assert(objects[1].flags&LV_OBJ_FLAG_HIDDEN);
 content.detach();content.detach();const int detached=mutations;content.paint(model);assert(mutations==detached);
 allocations=0;fail_at=3;BrickContent partial;assert(!partial.attach(&root));partial.detach();partial.paint(model);
 allocations=0;fail_at=-1;assert(partial.attach(&root));partial.detach();
}
''')


if __name__ == '__main__':
    unittest.main()
