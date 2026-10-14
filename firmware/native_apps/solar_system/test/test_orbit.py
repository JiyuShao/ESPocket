"""Production sphere renderer, motion, controlled input and bounded worker regressions."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]


def run(code, sources=('orbit_renderer.cpp', 'orbit_textures.cpp', 'orbit_motion.cpp'), extra_files=None, flags=()):
    with tempfile.TemporaryDirectory(prefix='orbit-test-') as d:
        cpp, binary = Path(d)/'test.cpp', Path(d)/'test'
        cpp.write_text(code)
        for name, content in (extra_files or {}).items():
            path=Path(d)/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(content)
        subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23','-Wall','-Wextra','-Werror','-pthread',
                        '-I',d,'-I',str(ROOT/'include'),'-I',str(ROOT/'src'),*flags,str(cpp),
                        *(str(ROOT/'src'/s) for s in sources),'-o',str(binary)],check=True)
        subprocess.run([str(binary)],check=True,timeout=45)


class OrbitTest(unittest.TestCase):
    def test_motion_settles_cancel_keeps_attitude_and_input_arbitration(self):
        run(r'''
#include <cassert>
#include <cmath>
#include "espocket/orbit_input.hpp"
using namespace espocket::orbit;
int main(){Motion motion;assert(motion.advance(33,{}));const auto entry=motion.attitude();assert(entry.longitude>0);
 motion.advance(33,{Touch::Phase::Press,233,233});motion.advance(33,{Touch::Phase::Move,253,240});
 auto drag=motion.attitude();assert(drag.longitude!=entry.longitude && drag.tilt!=0 && drag.lean!=0);
 motion.advance(33,{Touch::Phase::Release});const auto released=motion.attitude();assert(released.moving);
 bool final=false;for(int i=0;i<600;++i)final=motion.advance(33,{});assert(!final && !motion.attitude().moving);
 motion.advance(33,{Touch::Phase::Press,233,233});motion.advance(33,{Touch::Phase::Move,253,240});
 const auto before=motion.attitude();motion.cancel_touch();assert(motion.advance(60000,{}));assert(!motion.advance(33,{}));
 for(int i=0;i<100;++i)assert(!motion.advance(33,{Touch::Phase::Cancel})); // A blocked pointer must not redraw an idle sphere forever.
 motion.request_redraw();assert(motion.advance(33,{}));assert(!motion.advance(33,{}));
 assert(motion.attitude().longitude==before.longitude && motion.attitude().tilt==before.tilt && motion.attitude().lean==before.lean);
 Input input;assert(!input.read(true,false,1,{{233,200,1}},false).activity);
 input.read(true,false,2,{},false);auto press=input.read(true,false,3,{{233,200,1}},false);assert(press.activity);
 assert(!input.read(true,false,3,{},false).selection);assert(input.read(true,false,4,{},false).selection==Kind::Earth);
 input.cancel();input.read(true,false,5,{},true);
 assert(input.read(true,false,6,{{233,233,1}},true).touch.phase==Touch::Phase::Press);
 assert(input.read(true,false,7,{{253,233,1}},true).touch.phase==Touch::Phase::Move);
 assert(input.read(true,false,8,{{253,233,2}},true).touch.phase==Touch::Phase::Cancel);
 assert(!input.read(true,false,9,{{253,233,2}},true).activity);input.read(true,false,10,{},true);
 assert(input.read(false,true,11,{{233,233,1}},true).touch.phase==Touch::Phase::Cancel);
 assert(!input.read(true,false,12,{{233,233,1}},true).activity);input.read(true,false,13,{},false);
 input.read(true,false,14,{{233,200,1}},false);input.read(true,false,15,{{233,266,1}},false);
 assert(!input.read(true,false,16,{},false).selection); // A dragged menu press is not a new selection.
 for(int i=0;i<4;++i){assert(menu_hit(233,menu_centers[i])==static_cast<Kind>(i));assert(!menu_hit(108,menu_centers[i]+28));}
 assert(input.read(true,false,17,{{0,0,1}},true).touch.phase==Touch::Phase::Cancel);
}
''')

    def test_renderer_bounds_each_kind_orientation_and_cancel(self):
        run(r'''
#include <cassert>
#include <cmath>
#include <limits>
#include <set>
#include "espocket/orbit_renderer.hpp"
using namespace espocket::orbit;
uint64_t hash(const Frame&f){uint64_t h=0;for(auto p:f.pixels)h=h*31+p;return h;}
int main(){std::atomic_bool cancelled{false};std::set<uint64_t> images;
 for(auto kind:{Kind::Moon,Kind::Earth,Kind::Sun,Kind::Jupiter}){
  Renderer renderer;assert(renderer.initialize(kind));assert(!renderer.initialize(kind));auto frame=Frame::create();assert(frame);
  for(float tilt:{0.0f,1.5707963f,-1.5707963f,3.1415927f})for(float lean:{0.0f,1.5707963f,-2.5f}){
   assert(renderer.paint({.longitude=.25f,.tilt=tilt,.lean=lean,.moving=true},*frame,cancelled));
   assert(renderer.paint({.longitude=.25f,.tilt=tilt,.lean=lean},*frame,cancelled));int lit=0;
   for(int y=0;y<466;++y)for(int x=0;x<466;++x){auto px=frame->pixels[y*466+x];if(px)++lit;
    const float dx=x-center,dy=y-center; if(dx*dx+dy*dy>radius*radius+1)assert(!px);
   }assert(lit>130000);
  }
  images.insert(hash(*frame));auto before=hash(*frame);cancelled=true;assert(!renderer.paint({},*frame,cancelled));assert(hash(*frame)==before);cancelled=false;
  assert(!renderer.paint({.tilt=std::numeric_limits<float>::infinity()},*frame,cancelled));
 }assert(images.size()==4);Renderer invalid;assert(!invalid.initialize(static_cast<Kind>(99)));
}
''')

    def test_real_worker_pool_pending_pose_pause_stop_restart_and_allocation_failure(self):
        files={
            'esp_heap_caps.h':'''#pragma once
#include <cstddef>
constexpr int MALLOC_CAP_SPIRAM=1,MALLOC_CAP_8BIT=2;
void*heap_caps_malloc(size_t,int);void heap_caps_free(void*);
''',
            'esp_pthread.h':'''#pragma once
constexpr int ESP_OK=0;
struct esp_pthread_cfg_t{size_t stack_size=0;int prio=0,pin_to_core=0;const char*thread_name=nullptr;unsigned stack_alloc_caps=0;};
inline auto esp_pthread_get_default_config(){return esp_pthread_cfg_t{};}
inline int esp_pthread_get_cfg(esp_pthread_cfg_t*){return ESP_OK;}
inline int esp_pthread_set_cfg(const esp_pthread_cfg_t*){return ESP_OK;}
'''}
        run(r'''
#include <cassert>
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <thread>
#include "orbit_worker.hpp"
std::atomic<int>calls{0},fail_at{-1},live{0};
void*heap_caps_malloc(size_t n,int){if(calls++==fail_at)return nullptr;auto*p=std::malloc(n);if(p)++live;return p;}
void heap_caps_free(void*p){if(p){--live;std::free(p);}}
using namespace espocket::orbit;
uint64_t hash(const Frame&f){uint64_t h=0;for(auto p:f.pixels)h=h*31+p;return h;}
auto await(Worker&w){for(int i=0;i<3000;++i){if(auto f=w.take_frame())return f;std::this_thread::sleep_for(std::chrono::milliseconds(1));}assert(false);return std::shared_ptr<const Frame>{};}
int main(){Worker w;assert(w.pause());assert(w.resume());assert(w.start(Kind::Earth));assert(!w.start(Kind::Earth));
 w.submit({.moving=true});auto first=await(w);const auto initial=hash(*first);w.submit({.longitude=.25f});auto second=await(w);
 assert(hash(*first)==initial && first.get()!=second.get());w.submit({.longitude=.5f});w.submit({.longitude=.75f});
 std::this_thread::sleep_for(std::chrono::milliseconds(15));assert(!w.take_frame());first.reset();w.take_frame();auto latest=await(w);
 Renderer oracle;assert(oracle.initialize(Kind::Earth));auto image=Frame::create();std::atomic_bool no_cancel{false};assert(oracle.paint({.longitude=.75f},*image,no_cancel));assert(hash(*latest)==hash(*image));
 assert(w.pause());assert(!w.take_frame());latest.reset();second.reset();assert(w.resume());w.submit({});auto resumed=await(w);assert(hash(*resumed)==initial);resumed.reset();assert(w.stop());assert(w.stop());
 const int baseline=live;
 for(int failure=0;failure<3;++failure){fail_at=calls+failure;assert(w.start(Kind::Moon));for(int i=0;i<3000&&w.status()==Worker::Status::Starting;++i)std::this_thread::sleep_for(std::chrono::milliseconds(1));
  assert(w.status()==Worker::Status::Failed);assert(live==baseline);assert(w.pause());assert(w.resume());assert(w.stop());assert(live==baseline);
 }
 fail_at=-1;assert(w.start(Kind::Earth));w.submit({});auto fresh=await(w);assert(hash(*fresh)==initial);fresh.reset();assert(w.stop());
 {Worker nested;assert(nested.start(Kind::Sun));nested.submit({.tilt=1.5f,.moving=true});}assert(live==baseline);
}
''',sources=('orbit_renderer.cpp','orbit_textures.cpp','orbit_motion.cpp','orbit_worker.cpp'),extra_files=files,flags=('-DESP_PLATFORM',))

if __name__=='__main__':unittest.main()
