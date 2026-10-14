"""Execute production content against LVGL boundary doubles; no display claims."""
import unittest
from test_orbit import ROOT, run


class OrbitContentTest(unittest.TestCase):
    def test_menu_viewer_image_lifetime_cache_detach_and_each_partial_allocation(self):
        header=(ROOT/'src/orbit_content.hpp').read_text().split('namespace espocket {',1)[1]
        source=(ROOT/'src/orbit_content.cpp').read_text().split('namespace espocket {',1)[1]
        run(r'''
#include <cassert>
#include <expected>
#include <string>
#include "espocket/orbit_input.hpp"
struct lv_area_t{int x1,y1,x2,y2;};struct lv_event_t;using Callback=void(*)(lv_event_t*);
struct lv_obj_t{Callback cb=nullptr;void*data=nullptr;bool hidden=false;std::string text;int x=0,y=0,w=0,h=0;};
struct lv_event_t{lv_obj_t*obj;};struct lv_layer_t{};
struct lv_image_dsc_t{struct{int magic=0,cf=0,w=0,h=0,stride=0;}header;const uint8_t*data=nullptr;unsigned data_size=0;};
struct lv_draw_image_dsc_t{const void*src=nullptr;};
enum lv_obj_flag_t{LV_OBJ_FLAG_CLICKABLE=1,LV_OBJ_FLAG_SCROLLABLE=2,LV_OBJ_FLAG_HIDDEN=4};
constexpr int LV_OPA_COVER=255,LV_EVENT_DRAW_MAIN=1,LV_ALIGN_CENTER=0,LV_IMAGE_HEADER_MAGIC=9,LV_COLOR_FORMAT_RGB565=2;
lv_obj_t objects[16];int allocated=0,fail_at=-1,drops=0,draws=0,invalidations=0;lv_area_t drawn{};const lv_image_dsc_t*image=nullptr;
lv_obj_t*lv_obj_create(lv_obj_t*){if(allocated==fail_at)return nullptr;auto*p=&objects[allocated++];*p={};return p;}
auto lv_label_create(lv_obj_t*p){return lv_obj_create(p);}
void lv_obj_remove_style_all(lv_obj_t*){}void lv_obj_remove_flag(lv_obj_t*o,lv_obj_flag_t flags){if(flags&LV_OBJ_FLAG_HIDDEN)o->hidden=false;}
void lv_obj_add_flag(lv_obj_t*o,lv_obj_flag_t flags){if(flags&LV_OBJ_FLAG_HIDDEN)o->hidden=true;}
void lv_obj_set_size(lv_obj_t*o,int w,int h){o->w=w;o->h=h;}void lv_obj_center(lv_obj_t*o){o->x=0;o->y=0;}
int lv_color_black(){return 0;}int lv_color_hex(uint32_t x){return x;}
#define STYLE(fn) void fn(lv_obj_t*,int,int){}
STYLE(lv_obj_set_style_bg_color) STYLE(lv_obj_set_style_bg_opa) STYLE(lv_obj_set_style_text_color) STYLE(lv_obj_set_style_radius)
void lv_obj_add_event_cb(lv_obj_t*o,Callback cb,int,void*d){o->cb=cb;o->data=d;}
void lv_obj_remove_event_cb(lv_obj_t*o,Callback cb){assert(cb==o->cb);o->cb=nullptr;}
void lv_label_set_text(lv_obj_t*o,const char*t){o->text=t;}void lv_obj_align(lv_obj_t*o,int,int x,int y){o->x=x;o->y=y;}
void lv_image_cache_drop(lv_image_dsc_t*){++drops;}void lv_obj_invalidate(lv_obj_t*){++invalidations;}
void lv_obj_get_coords(lv_obj_t*,lv_area_t*a){*a={25,40,490,505};}
void*lv_event_get_user_data(lv_event_t*e){return e->obj->data;}lv_layer_t*lv_event_get_layer(lv_event_t*){return nullptr;}
void lv_draw_image_dsc_init(lv_draw_image_dsc_t*d){*d={};}
void lv_draw_image(lv_layer_t*,lv_draw_image_dsc_t*d,lv_area_t*a){image=static_cast<const lv_image_dsc_t*>(d->src);drawn=*a;++draws;}
namespace esp_brookesia::gui::lvgl{struct NativeContent{virtual~NativeContent()=default;virtual std::expected<void,std::string>attach(lv_obj_t*)=0;virtual void detach()noexcept=0;};}
namespace espocket {
''' + header + '\nnamespace espocket {\n' + source + r'''
int main(){using namespace espocket;lv_obj_t root;OrbitContent c;assert(c.attach(&root));
 for(int i=0;i<4;++i){const auto&o=objects[2+i*2];assert(o.w==250&&o.h==58&&o.y==orbit::menu_centers[i]-233&&!o.hidden);}
 c.show_viewer();for(int i=0;i<4;++i)assert(objects[2+i*2].hidden);assert(objects[1].text=="球体准备中");
 auto frame=orbit::Frame::create();std::weak_ptr<const orbit::Frame>weak=frame;c.paint(frame);frame.reset();assert(!weak.expired()&&drops==0&&objects[1].hidden);
 lv_event_t e{&objects[0]};objects[0].cb(&e);assert(draws==1&&drawn.x1==25&&drawn.y1==40&&drawn.y2==505);
 auto held=weak.lock();assert(image->data==reinterpret_cast<const uint8_t*>(held->pixels.data())&&image->data_size==466*466*2);held.reset();
 auto next=orbit::Frame::create();c.paint(next);assert(weak.expired()&&drops==1);std::weak_ptr<const orbit::Frame>last=next;next.reset();
 c.show_menu();assert(last.expired()&&drops==2&&!objects[1].hidden&&objects[1].text=="太阳系");
 c.show_viewer();c.show_failure();assert(!objects[1].hidden&&objects[1].text=="球体启动失败\n请返回后重试");
 c.paint(orbit::Frame::create());c.detach();assert(drops==3&&!objects[0].cb);c.detach();c.paint(orbit::Frame::create());assert(drops==3);
 for(int failure=0;failure<10;++failure){allocated=0;fail_at=failure;assert(!c.attach(&root));c.detach();c.detach();if(failure)assert(!objects[0].cb);}
}
''')

if __name__=='__main__':unittest.main()
