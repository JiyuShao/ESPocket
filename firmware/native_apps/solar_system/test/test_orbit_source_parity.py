"""Pixel-for-pixel regression against locked original sphere math and NASA textures."""
import hashlib
import json
import re
import unittest
from test_orbit import ROOT, run
UP = ROOT.parent/'badge/upstream'


def function(source,name):
    m=re.search(r'static (?:inline )?[^\n]+\b'+name+r'\([^;]*?\)\s*\{',source)
    start=source.index('{',m.start());end=start+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[m.start():end]


class OrbitParityTest(unittest.TestCase):
    def test_locked_source_resources_and_original_pixel_render(self):
        lock=json.loads((ROOT.parent/'badge/upstream.lock.json').read_text())['files']
        selected=['main/apps/orb.c','main/apps/orb.h','LICENSE','NOTICE']
        selected += [f'main/assets/orb_tex_{name}.h' for name in ('moon','earth','sun','jupiter')]
        for name in selected:
            data=(UP/name).read_bytes()
            self.assertEqual(len(data),lock[name]['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),lock[name]['sha256'])
            if name.startswith('main/assets/'):
                self.assertEqual((ROOT/'resources'/name.split('/')[-1]).read_bytes(),data)
        self.assertEqual((ROOT/'LICENSE').read_bytes(),(UP/'LICENSE').read_bytes())
        self.assertEqual((ROOT/'NOTICE').read_bytes(),(UP/'NOTICE').read_bytes())
        source=(UP/'main/apps/orb.c').read_text()
        build=function(source,'build_lut')
        build=build[build.index('    for (int i = 0;'):]
        # All tables present; reproduce the original computation with owned reference storage.
        build='static bool build_lut(){\n'+build
        render=function(source,'render')
        run(r'''
#include <cassert>
#include <cmath>
#include <cstring>
#include "espocket/orbit_renderer.hpp"
#include "orbit_textures.hpp"
namespace original {
constexpr int CX=233,CY=233,ORB_R=206,TEX_W=512,TEX_H=256;
constexpr int stride=2*ORB_R+1,px=stride*stride;
enum Kind {ORB_MOON,ORB_EARTH,ORB_SUN,ORB_JUPITER};Kind s_kind;
uint16_t framebuffer[466*466];uint16_t*s_fb=framebuffer;const uint16_t*s_tex;
int16_t s_lut_z[px];uint8_t s_lut_shade[px];
uint16_t u[px],v[px];uint16_t*s_lut_tu=u,*s_lut_tv=v;
int32_t s_span0[stride],s_span1[stride];float s_col_x[stride],s_asin_tab[1025];
float s_lon=0,s_tilt=0,s_lean=0,s_uv_tilt=0,s_uv_lean=0;bool s_uv_ok=false,s_coarse=false;
uint32_t s_render_us;int64_t esp_timer_get_time(){return 0;}
''' + function(source,'atan2_fast') + build + render + r'''
}
int main(){using namespace espocket::orbit;std::atomic_bool cancelled{false};
 for(int k=0;k<4;++k){Renderer production;auto kind=static_cast<Kind>(k);assert(production.initialize(kind));auto f=Frame::create();
  original::s_kind=static_cast<original::Kind>(k);original::s_tex=texture(kind);original::s_uv_ok=false;
  std::memset(original::s_fb,0,466*466*2);assert(original::build_lut());
  const Attitude poses[]={ {.moving=true},{.longitude=.25f},{.longitude=.75f,.moving=true},
   {.longitude=.125f,.tilt=1.5707963f,.lean=.75f,.moving=true},
   {.longitude=.125f,.tilt=1.5707963f,.lean=.75f},
   {.longitude=.50f,.tilt=1.5707963f,.lean=.75f,.moving=true},
   {.longitude=.50f,.tilt=-1.5707963f,.lean=-2.5f},
   {.longitude=.99f,.tilt=3.1415927f,.lean=1.5707963f,.moving=true},
   {.longitude=.99f,.tilt=3.1415927f,.lean=1.5707963f}};
  bool first=true;
  for(auto pose:poses){original::s_lon=pose.longitude;original::s_tilt=pose.tilt;original::s_lean=pose.lean;original::s_coarse=pose.moving && !first;first=false;
   assert(production.paint(pose,*f,cancelled));original::render();
   assert(std::memcmp(f->pixels.data(),original::s_fb,466*466*2)==0);
  }
 }
}
''',flags=('-Wno-tautological-pointer-compare',))

    def test_original_drag_friction_wrap_and_final_refinement(self):
        source=(UP/'main/apps/orb.c').read_text()
        # Execute the actual input callback and step from the locked original. GUI is a boundary stub.
        run(r'''
#include <cassert>
#include <cmath>
#include "espocket/orbit_renderer.hpp"
namespace original {
constexpr int CX=233,CY=233,ORB_R=206;
float s_lon=0,s_spin=.1f,s_tilt=0,s_tilt_v=0,s_lean=0,s_lean_v=0,s_uv_tilt=0,s_uv_lean=0;
bool s_dragging=false,s_dirty=true,s_coarse=false,s_uv_ok=false;uint16_t*s_lut_tu=nullptr;
int32_t s_drag_x=0,s_drag_y=0;uint32_t s_last_ms=0,tick=0;void*s_canvas=nullptr;
using lv_event_code_t=int;struct lv_event_t{int code;};struct lv_point_t{int x,y;};struct lv_indev_t{};struct lv_timer_t{};
constexpr int LV_EVENT_PRESSED=1,LV_EVENT_PRESSING=2,LV_EVENT_RELEASED=3;
lv_point_t point{};int lv_event_get_code(lv_event_t*e){return e->code;}
lv_indev_t*lv_indev_active(){static lv_indev_t in;return &in;}void lv_indev_get_point(lv_indev_t*,lv_point_t*p){*p=point;}
bool launcher_screen_is_off(){return false;}uint32_t lv_tick_get(){return tick;}
int64_t esp_timer_get_time(){return 0;}void render(){}void lv_obj_invalidate(void*){}void frame_tick(const char*,int64_t){}
''' + function(source,'touch_cb') + function(source,'step') + r'''
}
int main(){using namespace espocket::orbit;Motion production;
 const Touch touches[]={ {},{Touch::Phase::Press,233,233},{Touch::Phase::Move,270,240},
  {Touch::Phase::Move,285,190},{Touch::Phase::Move,220,175},{Touch::Phase::Move,130,290},{Touch::Phase::Release}};
 auto compare=[&](Touch touch){if(touch.phase!=Touch::Phase::None){original::point={touch.x,touch.y};
  original::lv_event_t e{touch.phase==Touch::Phase::Press?1:touch.phase==Touch::Phase::Move?2:3};original::touch_cb(&e);}
  production.advance(33,touch);original::tick+=33;original::step(nullptr);auto pose=production.attitude();
  assert(std::fabs(pose.longitude-original::s_lon)<1e-5f);assert(std::fabs(pose.tilt-original::s_tilt)<1e-5f);assert(std::fabs(pose.lean-original::s_lean)<1e-5f);
 };
 for(auto touch:touches)compare(touch);for(int i=0;i<600;++i)compare({});assert(!production.advance(33,{}));
}
''',flags=('-Wno-unused-parameter',))

if __name__=='__main__':unittest.main()
