"""Production content: image lifetime, local coordinates, invalidation, detach and failures."""
import unittest
from test_water import ROOT, run


class WaterContentTest(unittest.TestCase):
    def test_frame_lifetime_local_coordinates_cache_and_detach(self):
        header=(ROOT/'src/water_content.hpp').read_text().split('namespace espocket {',1)[1]
        source=(ROOT/'src/water_content.cpp').read_text().split('namespace espocket {',1)[1]
        run(r'''
#include <cassert>
#include <algorithm>
#include <expected>
#include <string>
#include "espocket/water_simulation.hpp"
struct lv_area_t {int x1,y1,x2,y2;};
struct lv_event_t;using Callback=void(*)(lv_event_t*);
struct lv_obj_t {Callback cb=nullptr;void*data=nullptr;};
struct lv_event_t {lv_obj_t*obj;};
struct lv_layer_t {};
struct lv_image_dsc_t {struct{int magic=0,cf=0,w=0,h=0,stride=0;}header;const uint8_t*data=nullptr;unsigned data_size=0;};
struct lv_draw_image_dsc_t {const void*src=nullptr;};
constexpr int LV_OBJ_FLAG_CLICKABLE=1,LV_OBJ_FLAG_SCROLLABLE=2,LV_OPA_COVER=255,LV_EVENT_DRAW_MAIN=1,LV_ALIGN_CENTER=0,LV_IMAGE_HEADER_MAGIC=9,LV_COLOR_FORMAT_RGB565=2;
lv_obj_t objects[8];int allocated=0,fail_at=-1,drops=0,draws=0;lv_area_t invalid{},drawn{};const lv_image_dsc_t*image=nullptr;
lv_obj_t*lv_obj_create(lv_obj_t*){if(allocated==fail_at)return nullptr;return &objects[allocated++];}
auto lv_label_create(lv_obj_t*p){return lv_obj_create(p);}
void lv_obj_remove_style_all(lv_obj_t*){}void lv_obj_remove_flag(lv_obj_t*,int){}void lv_obj_set_size(lv_obj_t*,int,int){}void lv_obj_center(lv_obj_t*){}
int lv_color_black(){return 0;}int lv_color_hex(uint32_t x){return x;}
#define STYLE(fn) void fn(lv_obj_t*,int,int){}
STYLE(lv_obj_set_style_bg_color) STYLE(lv_obj_set_style_bg_opa) STYLE(lv_obj_set_style_text_color)
void lv_obj_add_event_cb(lv_obj_t*o,Callback cb,int,void*d){o->cb=cb;o->data=d;}
void lv_obj_remove_event_cb(lv_obj_t*o,Callback cb){assert(cb==o->cb);o->cb=nullptr;}
void lv_label_set_text(lv_obj_t*,const char*){}void lv_obj_align(lv_obj_t*,int,int,int){}
void lv_image_cache_drop(lv_image_dsc_t*){++drops;}
void lv_obj_get_coords(lv_obj_t*,lv_area_t*a){*a={25,40,490,505};}
void lv_obj_invalidate_area(lv_obj_t*,lv_area_t*a){invalid=*a;}
void*lv_event_get_user_data(lv_event_t*e){return e->obj->data;}
lv_layer_t*lv_event_get_layer(lv_event_t*){return nullptr;}
void lv_draw_image_dsc_init(lv_draw_image_dsc_t*d){*d={};}
void lv_draw_image(lv_layer_t*,lv_draw_image_dsc_t*d,lv_area_t*a){image=static_cast<const lv_image_dsc_t*>(d->src);drawn=*a;++draws;}
namespace esp_brookesia::gui::lvgl {struct NativeContent {virtual~NativeContent()=default;virtual std::expected<void,std::string>attach(lv_obj_t*)=0;virtual void detach()noexcept=0;};}
namespace espocket {
''' + header + '\nnamespace espocket {\n' + source + r'''
int main(){using namespace espocket;lv_obj_t root;WaterContent content;assert(content.attach(&root));
 auto frame=water::Frame::create();frame->y0=180;frame->y1=420;std::weak_ptr<const water::Frame>weak=frame;
 content.paint(frame);frame.reset();assert(!weak.expired()&&drops==0&&invalid.y1==40&&invalid.y2==505);
 lv_event_t e{&objects[0]};objects[0].cb(&e);assert(draws==1&&drawn.x1==25&&drawn.y1==220&&drawn.y2==460);
 auto held=weak.lock();assert(image->data==reinterpret_cast<const uint8_t*>(held->pixels.data()+180*466));assert(image->header.h==241&&image->data_size==241*932);held.reset();
 auto next=water::Frame::create();next->y0=210;next->y1=390;content.paint(next);assert(weak.expired()&&drops==1&&invalid.y1==220&&invalid.y2==460);
 std::weak_ptr<const water::Frame>last=next;next.reset();content.detach();assert(last.expired()&&drops==2&&!objects[0].cb);content.detach();content.paint(water::Frame::create());assert(drops==2);
 allocated=0;fail_at=1;assert(!content.attach(&root));content.detach();assert(!objects[0].cb);
}
''')

if __name__=='__main__':unittest.main()
