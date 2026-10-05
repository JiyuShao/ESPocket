"""Run the real capture path against a cache that fragments the frame allocation."""
from pathlib import Path
import os,subprocess,tempfile,unittest
COMPONENT=Path(__file__).resolve().parents[1]
class CaptureCacheTest(unittest.TestCase):
    def test_capture_reclaims_cache_without_refilling_and_restores_all_exits(self):
        source=(COMPONENT/'src/display_screenshot.cpp').read_text()
        source='\n'.join(l for l in source.splitlines() if not l.startswith('#include "') or l=='#include "espocket/screenshot.hpp"')
        preamble=r'''
#include <cstdlib>
#include <cstring>
#include <cassert>
#include <cstdint>
#include <cstddef>
#define ESP_LOGI(...)
#define ESP_LOGW(...)
#define ESP_OK 0
#define CONFIG_BROOKESIA_SYSTEM_CORE_WORKER_PRIORITY 10
#define CONFIG_BROOKESIA_GUI_LVGL_DISPLAY_SOURCE_TASK_PRIORITY 6
using UBaseType_t=unsigned;
UBaseType_t task_priority=3;
UBaseType_t uxTaskPriorityGet(void*){return task_priority;}
void vTaskPrioritySet(void*,UBaseType_t p){task_priority=p;}
#define MALLOC_CAP_SPIRAM 1
#define MALLOC_CAP_8BIT 2
#define LV_COLOR_FORMAT_RGB565 1
#define LV_DISPLAY_RENDER_MODE_PARTIAL 1
#define LV_DISPLAY_ROTATION_0 0
#define LV_EVENT_FLUSH_START 1
#define PSA_SUCCESS 0
#define PSA_ALG_SHA_256 1
struct lv_cache_t {size_t max=262144;};lv_cache_t cache;
struct Global {lv_cache_t*img_cache=&cache;} global;
#define LV_GLOBAL_DEFAULT() (&global)
size_t lv_cache_get_max_size(lv_cache_t*c,void*){return c->max;}
void lv_image_cache_drop(const void*){}
void lv_image_cache_resize(uint32_t n,bool){cache.max=n;}
bool allocation_failure=false,hash_failure=false,lock_busy=false,incomplete=false;
int format=LV_COLOR_FORMAT_RGB565;bool locked=false;unsigned captures=0;
int esp_lv_adapter_lock(int){assert(task_priority>=10);if(lock_busy)return -1;assert(!locked);locked=true;return 0;}
void esp_lv_adapter_unlock(){assert(locked);locked=false;}
void*heap_caps_malloc(size_t n,int){if(cache.max||allocation_failure||n>8)return nullptr;return std::malloc(n);}
void heap_caps_free(void*p){std::free(p);}
struct lv_area_t {int x1,y1,x2,y2;};
struct Buffer {uint8_t*data;uint32_t data_size;struct {size_t stride;} header;};
uint8_t raw[]{0,248,224,7,31,0,0,248,224,7,31,0};Buffer buf{raw,12,{6}};
struct lv_display_t{} display;
struct lv_event_t {void*user_data;const lv_area_t*area;};
using Callback=void(*)(lv_event_t*);Callback callback=nullptr;void*context=nullptr;
void*lv_event_get_user_data(lv_event_t*e){return e->user_data;}
void*lv_event_get_target(lv_event_t*){return &display;}
const void*lv_event_get_param(lv_event_t*e){return e->area;}
const Buffer*lv_display_get_buf_active(lv_display_t*){return &buf;}
lv_display_t*lv_display_get_default(){return &display;}
int lv_display_get_color_format(lv_display_t*){return format;}
int lv_display_get_render_mode(lv_display_t*){return LV_DISPLAY_RENDER_MODE_PARTIAL;}
int lv_display_get_rotation(lv_display_t*){return 0;}
int lv_display_get_offset_x(lv_display_t*){return 0;}int lv_display_get_offset_y(lv_display_t*){return 0;}
int lv_display_get_horizontal_resolution(lv_display_t*){return 3;}int lv_display_get_vertical_resolution(lv_display_t*){return 2;}
unsigned lv_display_get_event_count(lv_display_t*){return callback?1:0;}
void lv_display_add_event_cb(lv_display_t*,Callback cb,int,void*u){callback=cb;context=u;}
void lv_display_remove_event_cb_with_user_data(lv_display_t*,Callback,void*){callback=nullptr;context=nullptr;}
void*lv_display_get_screen_active(lv_display_t*){return &display;}
void lv_obj_invalidate(void*){}
void lv_refr_now(lv_display_t*){assert(locked && cache.max==0);++captures;if(incomplete)return;lv_area_t a{0,0,2,1};lv_event_t e{context,&a};callback(&e);}
int psa_crypto_init(){return 0;}
struct psa_hash_operation_t{};
#define PSA_HASH_OPERATION_INIT {}
int psa_hash_setup(psa_hash_operation_t*,int){return 0;}
int psa_hash_update(psa_hash_operation_t*,const void*,size_t){return hash_failure?-1:0;}
int psa_hash_finish(psa_hash_operation_t*,unsigned char*p,size_t,size_t*s){std::memset(p,0,32);*s=32;return 0;}
int psa_hash_abort(psa_hash_operation_t*){return 0;}
'''
        tail=r'''
int main(){std::array<uint8_t,12> bytes;
 {auto r=espocket::capture_display_screenshot();assert(r && r->size==12 && r->pixels->read(0,bytes) && bytes[1]==248 && captures==1);}
 assert(task_priority==3 && cache.max==262144 && !locked && !callback);
 allocation_failure=true;assert(!espocket::capture_display_screenshot());assert(task_priority==3 && cache.max==262144 && !locked);allocation_failure=false;
 hash_failure=true;assert(!espocket::capture_display_screenshot());assert(task_priority==3 && cache.max==262144 && !locked && !callback);hash_failure=false;
 incomplete=true;assert(!espocket::capture_display_screenshot());assert(task_priority==3 && cache.max==262144 && !locked && !callback);incomplete=false;
 format=99;assert(!espocket::capture_display_screenshot());assert(task_priority==3 && cache.max==262144 && !locked);format=1;
 lock_busy=true;assert(!espocket::capture_display_screenshot());assert(task_priority==3 && cache.max==262144 && !locked);lock_busy=false;
 cache.max=0;assert(espocket::capture_display_screenshot());assert(task_priority==3 && cache.max==0 && !locked);
 task_priority=12;assert(espocket::capture_display_screenshot());assert(task_priority==12 && !locked);
}
'''
        with tempfile.TemporaryDirectory(prefix='espocket-capture-cache-') as d:
            path=Path(d);cpp=path/'capture.cpp';binary=path/'capture';cpp.write_text(preamble+source+tail)
            result=subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23','-I',str(COMPONENT/'include'),str(cpp),str(COMPONENT/'src/screenshot.cpp'),'-o',str(binary)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
if __name__=='__main__':unittest.main()
