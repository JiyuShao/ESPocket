"""Run the actual PNG decode call site with padded pixels and allocation failures."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare
SOURCE = ROOT / 'firmware/managed_components/espressif__esp_lv_decoder'
MANIFEST = ROOT / 'firmware/patches/espressif__esp_lv_decoder/0.4.3/manifest.json'


def exercise(source, directory, binary_support=True):
    text = (source / 'src/lvgl9/esp_lv_decoder.c').read_text()
    begin = text.rindex('static lv_draw_buf_t * png_decode_rgba(')
    if 'static lv_draw_buf_t * optimize_' in text:
        begin = text.index('static lv_draw_buf_t * optimize_')
    methods = text[begin:text.index('static lv_draw_buf_t * qoi_decode_qoi(', begin)]
    code = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#define LV_COLOR_FORMAT_ARGB8888 1
#define LV_COLOR_FORMAT_RGB565 2
#define LV_COLOR_FORMAT_RGB888 3
#define LV_COLOR_FORMAT_RGB565A8 4
#define LV_DRAW_SW_SUPPORT_RGB565A8 1
#define LV_STRIDE_AUTO 0
#define LV_IMAGE_SRC_FILE 1
#define LV_IMAGE_SRC_VARIABLE 2
#define ESP_OK 0
#define ESP_FAIL 1
#define ESP_ERR_NO_MEM 2
#define PNG_IMAGE_VERSION 1
#define PNG_FORMAT_BGRA 1
#define TAG "test"
#define ESP_GOTO_ON_ERROR(test,label,...) do{if((test)!=ESP_OK)goto label;}while(0)
typedef int esp_err_t;
typedef int lv_color_format_t;
typedef struct {unsigned width,height,version,format;} png_image;
typedef struct {const uint8_t *data;unsigned data_size;} lv_image_dsc_t;
typedef struct {int src_type;const void *src;} lv_image_decoder_dsc_t;
typedef struct {struct {unsigned w,h,stride;int cf;} header;uint8_t *data;unsigned data_size;} lv_draw_buf_t;
void *image_cache_draw_buf_handlers=NULL;
unsigned width=3,height=2,allocated=0,destroyed=0;int target=LV_COLOR_FORMAT_RGB565;
bool opaque=true,binary_alpha=false,fail_decode=false,fail_conversion=false;
uint8_t pixels[24]={0x00,0x00,0xff,0xff, 0x00,0xff,0x00,0xff, 0xff,0x00,0x00,0xff,
                    0x11,0x22,0x33,0xff, 0xa5,0x6d,0x29,0xff, 0xff,0xff,0xff,0xff};
int get_target_rgb_format(void){return target;}
const char*lv_fs_get_ext(const void*p){return "png";}
int lv_strcmp(const char*a,const char*b){return strcmp(a,b);}
uint8_t *alloc_file(const void*src,unsigned*size){*size=1;return calloc(1,1);}
bool png_dimensions_allowed(unsigned w,unsigned h){return w&&h;}
bool png_image_begin_read_from_memory(png_image *im,const void*p,unsigned size){im->width=width;im->height=height;return true;}
lv_draw_buf_t *lv_draw_buf_create_ex(void*handlers,unsigned w,unsigned h,int cf,int stride){
    if(cf!=LV_COLOR_FORMAT_ARGB8888 && fail_conversion)return NULL;
    lv_draw_buf_t *b=calloc(1,sizeof(*b));b->header.w=w;b->header.h=h;b->header.cf=cf;
    b->header.stride=(w*(cf==LV_COLOR_FORMAT_ARGB8888?4:2)+7)&~7u;
    b->data_size=b->header.stride*h+(cf==LV_COLOR_FORMAT_RGB565A8?b->header.stride/2*h:0);b->data=calloc(1,b->data_size);++allocated;return b;
}
void lv_draw_buf_destroy_user(void*handlers,lv_draw_buf_t*b){++destroyed;free(b->data);free(b);}
bool png_image_finish_read(png_image*im,void*bg,void*dest,int stride,void*map){
    // libpng row_stride is in components; zero selects tightly packed rows.
    const unsigned bytes=stride?stride:width*4;
    for(unsigned y=0;y<height;++y)memcpy((uint8_t*)dest+y*bytes,pixels+y*width*4,width*4);
    if(!opaque)((uint8_t*)dest)[bytes+3]=binary_alpha?0:239;
    return !fail_decode;
}
void png_image_free(png_image*im){}
''' + methods + r'''
int main(void){
 const uint8_t marker[1]={0};lv_image_dsc_t img={marker,1};lv_image_decoder_dsc_t dsc={LV_IMAGE_SRC_VARIABLE,&img};
 for(int from_file=0;from_file<2;++from_file){dsc.src_type=from_file?LV_IMAGE_SRC_FILE:LV_IMAGE_SRC_VARIABLE;dsc.src=from_file?(const void*)"test.png":(const void*)&img;
  lv_draw_buf_t *b=png_decode_rgba(&dsc);assert(b && b->header.cf==LV_COLOR_FORMAT_RGB565);
  for(unsigned y=0;y<height;++y)for(unsigned x=0;x<width;++x){const uint8_t*p=pixels+(y*width+x)*4;
   uint16_t expected=((uint16_t)(p[2]>>3)<<11)|((uint16_t)(p[1]>>2)<<5)|(p[0]>>3);
   uint16_t actual;memcpy(&actual,b->data+y*b->header.stride+x*2,2);assert(actual==expected);}
  lv_draw_buf_destroy_user(NULL,b);
 }
 dsc.src_type=LV_IMAGE_SRC_VARIABLE;dsc.src=&img;
 opaque=false;lv_draw_buf_t*b=png_decode_rgba(&dsc);assert(b && b->header.cf==LV_COLOR_FORMAT_ARGB8888);assert(b->data[b->header.stride+3]==239);lv_draw_buf_destroy_user(NULL,b);
 binary_alpha=true;
 for(int from_file=0;from_file<2;++from_file){
  dsc.src_type=from_file?LV_IMAGE_SRC_FILE:LV_IMAGE_SRC_VARIABLE;dsc.src=from_file?(const void*)"test.png":(const void*)&img;
  b=png_decode_rgba(&dsc);assert(b);
#if LV_DRAW_SW_SUPPORT_RGB565A8
  assert(b->header.cf==LV_COLOR_FORMAT_RGB565A8);
  for(unsigned y=0;y<height;++y)for(unsigned x=0;x<width;++x){
   const uint8_t*p=pixels+(y*width+x)*4;
   uint16_t actual;memcpy(&actual,b->data+y*b->header.stride+x*2,2);
   assert(actual==(((uint16_t)(p[2]>>3)<<11)|((uint16_t)(p[1]>>2)<<5)|(p[0]>>3)));
   assert(b->data[b->header.stride*height+y*b->header.stride/2+x]==((y==1&&x==0)?0:255));
  }
#else
  assert(b->header.cf==LV_COLOR_FORMAT_ARGB8888 && b->data[b->header.stride+3]==0);
#endif
  lv_draw_buf_destroy_user(NULL,b);
 }
 fail_conversion=true;b=png_decode_rgba(&dsc);assert(b && b->header.cf==LV_COLOR_FORMAT_ARGB8888 && b->data[b->header.stride+3]==0);lv_draw_buf_destroy_user(NULL,b);
 fail_conversion=false;binary_alpha=false;dsc.src_type=LV_IMAGE_SRC_VARIABLE;dsc.src=&img;
 opaque=true;target=LV_COLOR_FORMAT_RGB888;b=png_decode_rgba(&dsc);assert(b&&b->header.cf==LV_COLOR_FORMAT_ARGB8888);lv_draw_buf_destroy_user(NULL,b);
 target=LV_COLOR_FORMAT_RGB565;fail_conversion=true;b=png_decode_rgba(&dsc);assert(b&&b->header.cf==LV_COLOR_FORMAT_ARGB8888);lv_draw_buf_destroy_user(NULL,b);
 fail_conversion=false;fail_decode=true;assert(!png_decode_rgba(&dsc));
 assert(allocated==destroyed);
}
'''
    directory=Path(directory);cpp=directory/'png.c';binary=directory/'png';cpp.write_text(code.replace('#define LV_DRAW_SW_SUPPORT_RGB565A8 1', '#define LV_DRAW_SW_SUPPORT_RGB565A8 '+str(int(binary_support))))
    subprocess.run([os.environ.get('CC','clang'),'-std=c11',str(cpp),'-o',str(binary)],check=True)
    return subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)


class PngOpaqueDecodeTest(unittest.TestCase):
    def test_real_decode_format_pixels_alpha_padding_and_failure_cleanup(self):
        with tempfile.TemporaryDirectory(prefix='espocket-opaque-png-') as directory:
            self.assertNotEqual(exercise(SOURCE,directory).returncode,0)
            patched=prepare(SOURCE,MANIFEST,Path(directory)/'patched')
            for supported in [True, False]:
                result=exercise(patched,directory,binary_support=supported)
                self.assertEqual(result.returncode,0,result.stderr)
