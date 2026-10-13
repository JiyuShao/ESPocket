"""Production solver, renderer and worker tests; no simulated IMU or device claims."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]


def run(code, sources=('water_simulation.cpp',), extra_files=None, flags=()):
    with tempfile.TemporaryDirectory(prefix='water-test-') as d:
        cpp, binary = Path(d) / 'test.cpp', Path(d) / 'test'
        cpp.write_text(code)
        for name, contents in (extra_files or {}).items():
            (Path(d) / name).write_text(contents)
        subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-Wall', '-Wextra', '-Werror',
                        '-pthread', '-I', d, '-I', str(ROOT / 'include'), '-I', str(ROOT / 'src'),
                        *flags, str(cpp), *(str(ROOT / 'src' / s) for s in sources), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=45)


class WaterTest(unittest.TestCase):
    def test_particles_boat_touch_bounds_and_per_buffer_clearing(self):
        # Also run the actual incremental painter with two exclusive image histories.
        run(r'''
#include <cassert>
#include <cmath>
#include <algorithm>
#include "espocket/water_simulation.hpp"
using namespace espocket::water;
int main() {
 Simulation model, other; assert(model.initialize() && other.initialize()); assert(!model.initialize());
 auto a=Frame::create(), b=Frame::create(); assert(a && b);
 std::atomic_bool cancelled{false};
 const auto initial=model.diagnostics(); assert(initial.finite && initial.escaped==0);
 for(int i=0;i<100;++i) {
  auto &frame= i%2 ? *a : *b;
  const Impulse touch = i%17==0 ? Impulse{.x=233,.y=330,.vx=350,.vy=-350,.burst=260,.active=true} : Impulse{};
  assert(model.advance(i%3 ? 33 : 5000,touch,frame,cancelled));
  const auto d=model.diagnostics(); assert(d.finite && d.escaped==0 && !d.neighbor_overflow);
  assert(std::hypot(d.boat_x-center,d.boat_y-center)<=bowl_radius-39);
  assert(frame.y0>=0 && frame.y1<canvas_size && frame.y1>=frame.y0);
  int painted=0;
  for(int y=0;y<canvas_size;++y)for(int x=0;x<canvas_size;++x) {
   auto color=frame.pixels[y*canvas_size+x];
   if(!color)continue;
   ++painted;assert(y>=frame.y0 && y<=frame.y1);
   // Outside the current column's water extent and boat bounds there must be no stale pixels.
   const bool water=frame.previous_top[x]<=frame.previous_bottom[x] && y>=frame.previous_top[x] && y<=frame.previous_bottom[x];
   const bool boat=x>=frame.boat_x0 && x<=frame.boat_x1 && y>=frame.boat_y0 && y<=frame.boat_y1;
   assert(water || boat);
  }
  assert(painted>1000);
 }
 assert(model.diagnostics().fingerprint!=initial.fingerprint);
 assert(other.diagnostics().fingerprint==initial.fingerprint);
 const auto before=model.diagnostics().fingerprint; cancelled=true;
 assert(!model.advance(33,{},*a,cancelled));assert(model.diagnostics().fingerprint==before);
}
''')

    def test_input_release_cancel_duplicate_and_track_identity(self):
        run(r'''
#include <cassert>
#include "espocket/water_input.hpp"
using namespace espocket::water;
int main(){ Input input;
 assert(!input.read(true,false,1,{{233,320,1}}).active);
 assert(!input.read(true,false,2,{}).active);
 auto poke=input.read(true,false,3,{{233,320,1}});assert(poke.active && poke.burst>0);
 assert(!input.read(true,false,3,{{233,340,1}}).active);
 auto drag=input.read(true,false,4,{{253,330,1}});assert(drag.active && drag.vx>0 && drag.vy>0);
 assert(!input.read(true,false,5,{{255,340,2}}).active); // A new track cannot inherit a drag.
 assert(!input.read(true,false,6,{{255,340,2}}).active);
 input.read(true,false,7,{}); assert(input.read(true,false,8,{{233,320,2}}).active);
 assert(!input.read(false,true,9,{{233,340,2}}).active);
 assert(!input.read(true,false,10,{{233,340,2}}).active);
 input.read(true,false,11,{}); assert(!input.read(true,false,12,{{0,0,3}}).active);
 input.cancel();assert(!input.read(true,false,13,{{233,320,1}}).active);
}
''')

    def test_worker_pause_inflight_stop_restart_failure_and_immutable_frames(self):
        # Real std::thread/mutex/cv. Substitute only ESP allocator and thread configuration boundary.
        files = {
            'esp_heap_caps.h': '''#pragma once
#include <cstddef>
constexpr int MALLOC_CAP_SPIRAM=1,MALLOC_CAP_8BIT=2;
void*heap_caps_malloc(size_t,int);void heap_caps_free(void*);
''',
            'esp_pthread.h': '''#pragma once
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
#include "water_worker.hpp"
std::atomic<int> allocations{0},fail_at{-1},live{0};
void*heap_caps_malloc(size_t n,int){int call=allocations++;if(call==fail_at)return nullptr;auto*p=std::malloc(n);if(p)++live;return p;}
void heap_caps_free(void*p){if(p){--live;std::free(p);}}
using namespace espocket::water;
uint64_t hash(const Frame&f){uint64_t h=0;for(auto p:f.pixels)h=h*31+p;return h;}
auto await(Worker&w){for(int i=0;i<3000;++i){if(auto f=w.take_frame())return f;std::this_thread::sleep_for(std::chrono::milliseconds(1));}assert(false);return std::shared_ptr<const Frame>{};}
int main(){
 Worker w;assert(w.start());assert(!w.start());w.submit(1000,{});auto first=await(w);const auto original=hash(*first);
 w.submit(1033,{.x=233,.y=330,.vx=200,.vy=-200,.active=true});auto second=await(w);assert(hash(*first)==original && first.get()!=second.get());
 // Both slots held: retain the coalesced input until a slot becomes available.
 const Impulse held_touch{.x=233,.y=330,.vx=-300,.vy=-300,.burst=260,.active=true};
 w.submit(1066,held_touch);w.submit(1099,{});first.reset();w.submit(1099,{});auto third=await(w);
 Simulation oracle;assert(oracle.initialize());auto oracle_a=Frame::create(),oracle_b=Frame::create();std::atomic_bool no_cancel{false};
 assert(oracle.advance(33,{},*oracle_a,no_cancel));
 assert(oracle.advance(33,{.x=233,.y=330,.vx=200,.vy=-200,.active=true},*oracle_b,no_cancel));
 assert(oracle.advance(66,held_touch,*oracle_a,no_cancel));assert(hash(*third)==hash(*oracle_a));
 oracle_a.reset();oracle_b.reset(); // oracle's state is still independently owned until this scope exits.
 assert(w.pause());assert(!w.take_frame());third.reset();second.reset();
 assert(w.resume());w.submit(60000,{});auto resumed=await(w);assert(resumed);
 resumed.reset();w.submit(60033,{});assert(w.pause());assert(w.stop() && live==1);assert(w.stop());
 // Partial allocations fail on the worker; stop releases all successful allocations.
 for(int failure=0;failure<3;++failure){fail_at=allocations.load()+failure;assert(w.start());
  for(int i=0;i<3000&&w.status()==Worker::Status::Starting;++i)std::this_thread::sleep_for(std::chrono::milliseconds(1));
  assert(w.status()==Worker::Status::Failed);assert(w.pause());assert(w.resume());assert(w.stop());assert(live==1);
 }
 fail_at=-1;assert(w.start());w.submit(1000,{});auto fresh=await(w);assert(hash(*fresh)==original);fresh.reset();assert(w.stop() && live==1);
 // Destruction joins an in-flight update without a GUI dependency.
 {Worker nested;assert(nested.start());nested.submit(1000,{});}assert(live==1);
}
''', sources=('water_simulation.cpp', 'water_worker.cpp'), extra_files=files, flags=('-DESP_PLATFORM',))

if __name__ == '__main__': unittest.main()
