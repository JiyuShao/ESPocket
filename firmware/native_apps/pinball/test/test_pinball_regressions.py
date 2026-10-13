"""Regressions found while comparing the locked original and LVGL pointer lifetimes."""
import unittest
from test_pinball_model import ROOT, run


class PinballRegressionTest(unittest.TestCase):
    def test_substep_flipper_collision_speed_and_one_release_restart(self):
        run(r'''
#include <cassert>
#include <cmath>
#include <array>
#include <vector>
#define private public
#include "espocket/pinball_model.hpp"
#undef private
using namespace espocket::pinball;
int main(){Model m;int seq=0;
 m.advance(0,true,false,++seq,{});m.advance(0,true,false,++seq,{{233,390,1}});m.advance(0,true,false,++seq,{});
 auto&s=m.state_;s.x=233;s.y=233;s.vx=0;s.vy=0;
 m.advance(20,true,false,++seq,{{100,390,2},{360,390,3}});
 assert(std::fabs(s.flippers[0].angle-9)<0.001 && std::fabs(s.flippers[1].angle-171)<0.001);
 // Free travel is capped before collision response (same point as the original).
 s.x=233;s.y=220;s.vx=200;s.vy=0;m.advance(20,true,false,++seq,{});assert(std::hypot(s.vx,s.vy)<=14.001);
 // A stationary contact still resolves on subsequent substeps after the one motion kick.
 std::vector<Tone>tones;std::array<float,2>omega{};std::array<bool,2>kicked{true,false};
 auto&f=s.flippers[0];f.angle=0;s.x=f.px+30;s.y=f.py;s.vx=s.vy=0;
 assert(m.substep(tones,omega,kicked));assert(std::fabs(s.y-(f.py-13.5f))<0.001);
 s.phase=Phase::GameOver;s.balls=0;m.cancel_input();
 m.advance(0,true,false,++seq,{});m.advance(0,true,false,++seq,{{233,390,4}});
 m.advance(0,true,false,++seq,{});m.advance(0,true,false,++seq,{{100,390,5}});
 assert(s.phase==Phase::Playing&&s.balls==3&&s.flippers[0].on);
}
''')

    def test_each_line_keeps_its_own_borrowed_points(self):
        header=(ROOT/'src/pinball_content.hpp').read_text().split('namespace espocket {',1)[1]
        methods=(ROOT/'src/pinball_content.cpp').read_text().split('namespace espocket {',1)[1]
        run(r'''
#include <cassert>
#include <cmath>
#include <expected>
#include <optional>
#include <string>
#include "espocket/pinball_model.hpp"
using lv_value_precise_t=float;
struct lv_point_precise_t {float x,y;};
struct lv_obj_t {int w=0,h=0;const lv_point_precise_t*points=nullptr;};
lv_obj_t objects[64];int allocations=0,fail_at=-1;
constexpr int LV_OBJ_FLAG_CLICKABLE=1,LV_OBJ_FLAG_SCROLLABLE=2,LV_OBJ_FLAG_HIDDEN=4,LV_OPA_COVER=255,LV_PART_MAIN=0,LV_RADIUS_CIRCLE=32767,LV_ALIGN_CENTER=0;
lv_obj_t*lv_obj_create(lv_obj_t*){if(allocations==fail_at)return nullptr;return &objects[allocations++];}
auto lv_arc_create(lv_obj_t*p){return lv_obj_create(p);}auto lv_label_create(lv_obj_t*p){return lv_obj_create(p);}auto lv_line_create(lv_obj_t*p){return lv_obj_create(p);}
void lv_obj_remove_style_all(lv_obj_t*){}void lv_obj_remove_flag(lv_obj_t*,int){}void lv_obj_add_flag(lv_obj_t*,int){}
void lv_obj_set_size(lv_obj_t*o,int w,int h){o->w=w;o->h=h;}
void lv_obj_set_pos(lv_obj_t*,int,int){}void lv_obj_center(lv_obj_t*){}void lv_obj_align(lv_obj_t*,int,int,int){}
void lv_arc_set_value(lv_obj_t*,int){}void lv_arc_set_bg_angles(lv_obj_t*,int,int){}
int lv_color_hex(uint32_t v){return v;}int lv_color_white(){return 0xffffff;}
#define STYLE(fn) void fn(lv_obj_t*,int,int){}
STYLE(lv_obj_set_style_bg_opa) STYLE(lv_obj_set_style_bg_color) STYLE(lv_obj_set_style_radius)
STYLE(lv_obj_set_style_arc_width) STYLE(lv_obj_set_style_arc_color) STYLE(lv_obj_set_style_text_color)
STYLE(lv_obj_set_style_line_width) STYLE(lv_obj_set_style_line_color) STYLE(lv_obj_set_style_line_rounded)
void lv_line_set_points(lv_obj_t*o,const lv_point_precise_t*p,int){o->points=p;}
void lv_label_set_text(lv_obj_t*,const char*){}void lv_label_set_text_fmt(lv_obj_t*,const char*,...){}
namespace esp_brookesia::gui::lvgl {struct NativeContent {virtual~NativeContent()=default;virtual std::expected<void,std::string>attach(lv_obj_t*)=0;virtual void detach()noexcept=0;};}
namespace espocket {
''' + header + '\nnamespace espocket {\n' + methods + r'''
int main(){using namespace espocket;lv_obj_t root;PinballContent content;pinball::Model model;
 assert(content.attach(&root));assert(objects[1].w==437);
 auto*left=objects[11].points;auto*right=objects[12].points;
 assert(left && right && left!=right && left[0].x==92 && right[0].x==374);
 const float right_tip=right[1].x;
 auto&s=const_cast<pinball::State&>(model.state());s.flippers[0].angle-=15;content.paint(model);
 assert(right[1].x==right_tip && objects[11].points==left && objects[12].points==right);
 content.detach();content.detach();content.paint(model);
 allocations=0;fail_at=12;assert(!content.attach(&root));content.detach();
}
''')

if __name__=='__main__':unittest.main()
