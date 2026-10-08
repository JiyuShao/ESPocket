"""Execute GUI Owner policy admission, cache protection, statistics and release."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]


class ImageDecodingOwnerTest(unittest.TestCase):
    def test_real_policy_preserves_decoders_and_bounds_cache(self):
        sys.path.insert(0, str(ROOT / 'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='espocket-decode-owner-') as directory:
            root = Path(directory)
            gui = prepare(ROOT/'firmware/managed_components/espressif__brookesia_gui_lvgl',
                          ROOT/'firmware/patches/espressif__brookesia_gui_lvgl/0.8.5/manifest.json', root/'gui')
            def stub(path, text):
                target = root/'stubs'/path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text)
            stub('lvgl.h', r'''
#pragma once
#include <cstdint>
#include <cstddef>
enum lv_result_t { LV_RESULT_INVALID, LV_RESULT_OK };
constexpr int LV_IMAGE_SRC_FILE=1, LV_IMAGE_SRC_VARIABLE=2, LV_COLOR_FORMAT_ARGB8888=3;
struct lv_image_decoder_t;
struct lv_image_decoder_dsc_t { int src_type; const void* src; struct {uint32_t w,h;} header; struct {bool no_cache=false;} args; };
using lv_image_decoder_open_f_t=lv_result_t(*)(lv_image_decoder_t*,lv_image_decoder_dsc_t*);
struct lv_image_decoder_t {lv_image_decoder_open_f_t open_cb;};
struct lv_image_dsc_t {const uint8_t* data; size_t data_size;};
extern lv_image_decoder_t decoders[9]; extern int count, drops, resizes, originals; extern uint64_t clock_us;
inline lv_image_decoder_t* lv_image_decoder_get_next(lv_image_decoder_t* d){int i=d?int(d-decoders)+1:0;return i<count?&decoders[i]:nullptr;}
inline void lv_image_decoder_set_open_cb(lv_image_decoder_t* d,lv_image_decoder_open_f_t f){d->open_cb=f;}
inline void lv_image_cache_resize(uint32_t,bool){++resizes;}
inline void lv_image_cache_drop(void*){++drops;}
inline uint32_t lv_draw_buf_width_to_stride(uint32_t w,int){return w*4;}
''')
            stub('src/draw/lv_image_decoder_private.h', '#include "lvgl.h"\n')
            stub('src/misc/cache/instance/lv_image_cache.h', '#include "lvgl.h"\n')
            stub('esp_heap_caps.h', '#pragma once\n#include <cstdint>\nconstexpr int MALLOC_CAP_SPIRAM=1;\nextern uint64_t largest,free_bytes;\ninline uint64_t heap_caps_get_largest_free_block(int){return largest;}\ninline uint64_t heap_caps_get_free_size(int){return free_bytes;}\n')
            stub('esp_timer.h', '#pragma once\n#include <cstdint>\nextern uint64_t clock_us;\ninline uint64_t esp_timer_get_time(){return clock_us;}\n')
            harness = r'''
#include <cassert>
#include "lvgl.h"
#include "brookesia/gui_lvgl/image_decoding.hpp"
using namespace esp_brookesia::gui::lvgl;
lv_image_decoder_t decoders[9]; int count=0,drops=0,resizes=0,originals=0;
uint64_t largest=100000,free_bytes=100000,clock_us=0;bool fail=false;
lv_result_t original(lv_image_decoder_t*,lv_image_decoder_dsc_t*){++originals;clock_us+=7;return fail?LV_RESULT_INVALID:LV_RESULT_OK;}
lv_result_t newer(lv_image_decoder_t*,lv_image_decoder_dsc_t*){return LV_RESULT_INVALID;}
int main(){
 assert(!configure_image_decoding({100,10})); assert(!resizes);
 count=9;for(auto &d:decoders)d.open_cb=original;
 assert(!configure_image_decoding({100,10})); assert(!resizes);
 for(auto &d:decoders)assert(d.open_cb==original);
 count=2;assert(configure_image_decoding({100,10}));
 auto wrapped=decoders[0].open_cb;assert(wrapped!=original);
 assert(!configure_image_decoding({100,10}));assert(decoders[0].open_cb==wrapped);
 lv_image_decoder_dsc_t png{LV_IMAGE_SRC_FILE,"photo.png",{10,10},{}};
 set_image_decode_statistics_enabled(true);
 assert(wrapped(&decoders[0],&png)==LV_RESULT_OK && png.args.no_cache && !drops);
 auto s=take_image_decode_statistics();assert(s.attempts==1 && s.successes==1 && s.total_us==7);
 assert(take_image_decode_statistics().attempts==0);
 fail=true;assert(wrapped(&decoders[0],&png)==LV_RESULT_INVALID);fail=false;
 s=take_image_decode_statistics();assert(s.attempts==1 && s.successes==0);
 const uint8_t signature[]{137,80,78,71,13,10,26,10};lv_image_dsc_t image{signature,8};
 lv_image_decoder_dsc_t variable{LV_IMAGE_SRC_VARIABLE,&image,{2,2},{}};
 assert(wrapped(&decoders[0],&variable)==LV_RESULT_OK);assert(take_image_decode_statistics().attempts==1);
 lv_image_decoder_dsc_t jpg{LV_IMAGE_SRC_FILE,"photo.jpg",{10,10},{}};
 assert(wrapped(&decoders[0],&jpg)==LV_RESULT_OK && jpg.args.no_cache);
 assert(take_image_decode_statistics().attempts==0);
 png.args.no_cache=false;png.header={2,2};largest=8;
 assert(wrapped(&decoders[0],&png)==LV_RESULT_OK && !png.args.no_cache && drops==1);
 assert(take_image_decode_statistics().pressure_evictions==1);
 largest=100000;free_bytes=20;wrapped(&decoders[0],&png);assert(drops==2);
 free_bytes=100000;wrapped(&decoders[0],&png);assert(drops==2);
 set_image_decode_statistics_enabled(false);wrapped(&decoders[0],&png);
 assert(take_image_decode_statistics().attempts==0);
 // A later Owner must not be overwritten when this policy is released.
 decoders[1].open_cb=newer;release_image_decoding();
 assert(decoders[0].open_cb==original && decoders[1].open_cb==newer);
 assert(configure_image_decoding({0,0}));release_image_decoding();
 assert(decoders[0].open_cb==original && decoders[1].open_cb==newer);
}
'''
            (root/'test.cpp').write_text(harness)
            binary=root/'test'
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23','-DESP_PLATFORM',
                            '-I'+str(root/'stubs'),'-I'+str(gui/'include'),str(gui/'src/image_decoding.cpp'),str(root/'test.cpp'),'-o',str(binary)],check=True)
            subprocess.run([str(binary)],check=True,timeout=10)


if __name__ == '__main__':
    unittest.main()
