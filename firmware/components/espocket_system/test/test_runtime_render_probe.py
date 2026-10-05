"""Execute the real PNG observer: successful misses, failures, bounds and forwarding."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[4]

class RuntimeRenderProbeTest(unittest.TestCase):
    def test_real_decoder_wrapper_counts_only_png_and_preserves_forwarding(self):
        source=(ROOT/'firmware/components/espocket_system/src/runtime_render_probe.cpp').read_text()
        actual=source[source.index('bool is_png('):source.index('#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE\nvoid report()')]
        harness=r'''
#include <algorithm>
#include <array>
#include <cstring>
#include <cstdint>
#include <cassert>
enum lv_result_t{LV_RESULT_OK,LV_RESULT_INVALID};
enum Src{LV_IMAGE_SRC_FILE,LV_IMAGE_SRC_VARIABLE};
struct lv_image_decoder_t{};
struct lv_image_dsc_t{const uint8_t*data;uint32_t data_size;};
struct lv_image_decoder_dsc_t{Src src_type;const void*src;struct{unsigned w,h;}header;struct{bool no_cache=false;}args;};
using lv_image_decoder_open_f_t=lv_result_t(*)(lv_image_decoder_t*,lv_image_decoder_dsc_t*);
struct DecoderHook{lv_image_decoder_t*decoder;lv_image_decoder_open_f_t open;};
std::array<DecoderHook,8> hooks{};char app[]="test";
constexpr uint32_t CACHE_BYTES=1024;constexpr int LV_COLOR_FORMAT_ARGB8888=0;
constexpr uint64_t DECODE_HEADROOM_BYTES=65536;constexpr int MALLOC_CAP_SPIRAM=1;
uint64_t heap_free=1000000,heap_largest=1000000,pressure_evictions=0;unsigned dropped=0;
uint64_t heap_caps_get_free_size(int){return heap_free;}
uint64_t heap_caps_get_largest_free_block(int){return heap_largest;}
void lv_image_cache_drop(const void*src){assert(src==nullptr);++dropped;}
unsigned lv_draw_buf_width_to_stride(unsigned w,int){return w*4;}
uint64_t png_attempts=0,png_success=0,png_us=0,png_max_us=0;
int64_t clock_us=0;int64_t esp_timer_get_time(){return clock_us;}
unsigned forwarded=0;bool fail=false;
lv_result_t original(lv_image_decoder_t*,lv_image_decoder_dsc_t*){++forwarded;clock_us+=100;return fail?LV_RESULT_INVALID:LV_RESULT_OK;}
'''+actual+r'''
int main(){
 lv_image_decoder_t decoder,other;hooks[0]={&decoder,original};
 const uint8_t signature[]{137,80,78,71,13,10,26,10};lv_image_dsc_t image{signature,8};
 lv_image_decoder_dsc_t dsc{LV_IMAGE_SRC_VARIABLE,&image,{8,8}};
 assert(measured_open(&decoder,&dsc)==LV_RESULT_OK);assert(!dsc.args.no_cache);
 assert(measured_open(&decoder,&dsc)==LV_RESULT_OK);
#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE
 assert(png_attempts==2 && png_success==2 && png_us==200 && png_max_us==100);
#endif
 dsc.header={32,32};assert(measured_open(&decoder,&dsc)==LV_RESULT_OK && dsc.args.no_cache);
 fail=true;assert(measured_open(&decoder,&dsc)==LV_RESULT_INVALID);
#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE
 assert(png_attempts==4 && png_success==3);
#endif
 dsc.src_type=LV_IMAGE_SRC_FILE;dsc.src="image.jpg";dsc.args.no_cache=false;fail=false;
 assert(measured_open(&decoder,&dsc)==LV_RESULT_OK);assert(forwarded==5 && dsc.args.no_cache);
 dsc.src="image.png";assert(measured_open(&decoder,&dsc)==LV_RESULT_OK);
#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE
 assert(png_attempts==5 && png_success==4);
#endif
 assert(measured_open(&other,&dsc)==LV_RESULT_INVALID && forwarded==6);
 app[0]=0;assert(measured_open(&decoder,&dsc)==LV_RESULT_OK);assert(forwarded==7);
#if CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE
 assert(png_attempts==5);
#else
 assert(png_attempts==0);
#endif
 // Fragmentation and low total memory each evict retained entries, also
 // with diagnostics disabled. Adequate memory leaves the cache intact.
 assert(dropped==0);heap_largest=100;
 assert(measured_open(&decoder,&dsc)==LV_RESULT_OK);assert(dropped==1);
 heap_largest=1000000;heap_free=100;
 assert(measured_open(&decoder,&dsc)==LV_RESULT_OK);assert(dropped==2);
 heap_free=1000000;
 assert(measured_open(&decoder,&dsc)==LV_RESULT_OK);assert(dropped==2);
}
'''
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory);src=path/'main.cpp';src.write_text(harness);binary=path/'test'
            for profile in [0,1]:
                with self.subTest(profile=profile):
                    compile_result=subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23',f'-DCONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE={profile}',str(src),'-o',str(binary)],capture_output=True,text=True)
                    self.assertEqual(compile_result.returncode,0,compile_result.stderr)
                    result=subprocess.run([str(binary)],capture_output=True,text=True)
                    self.assertEqual(result.returncode,0,result.stderr)
