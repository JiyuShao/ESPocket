"""Verify the production per-mount delivery gate and existing Shell arbiter."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class NativePointerDeliveryTest(unittest.TestCase):
    def test_cancel_resume_and_two_fingers(self):
        with tempfile.TemporaryDirectory(prefix='native-pointer-') as directory:
            work = Path(directory)
            component = 'espressif__brookesia_gui_interface'
            gui = prepare(ROOT / 'firmware/managed_components' / component,
                          ROOT / 'firmware/patches' / component / '0.8.2/manifest.json', work / 'gui')
            source = work / 'test.cpp'
            source.write_text(r'''
#include <cassert>
#include "brookesia/gui_interface/native_pointer.hpp"
#include "espocket/shell_gesture.hpp"
using namespace esp_brookesia::gui;
NativePointerFrame sample(uint32_t seq, bool pressed=false) {
    NativePointerFrame f;f.sequence=seq;f.valid=true;
    if(pressed)f.points={{10,20,1},{30,40,2}};
    return f;
}
int main(){
    NativePointerDelivery delivery;
    assert(delivery.filter(sample(1,true),1).cancelled);
    assert(delivery.filter(sample(1),1).cancelled); // same-sequence empty is not acknowledgement
    assert(!delivery.filter(sample(2),1).cancelled);
    auto two=delivery.filter(sample(3,true),1);assert(!two.cancelled && two.points.size()==2);
    auto one=sample(4,true);one.points.pop_back();assert(delivery.filter(one,1).points.size()==1);
    auto denied=delivery.filter(sample(5,true),std::nullopt);assert(denied.cancelled && denied.points.empty());
    assert(delivery.filter(sample(6,true),1).cancelled);
    assert(!delivery.filter(sample(7),1).cancelled);
    assert(delivery.filter(sample(8,true),1).points.size()==2);
    // An overlay was opened AND closed while the App did not poll.
    assert(delivery.filter(sample(9,true),2).cancelled);
    assert(!delivery.filter(sample(10),2).cancelled);
    auto invalid=sample(11,true);invalid.valid=false;assert(delivery.filter(invalid,2).cancelled);
    assert(delivery.filter(sample(12,true),2).cancelled);
    assert(!delivery.filter(sample(13),2).cancelled);
    // Sequence wrap does not use an unsafe ordered comparison.
    assert(delivery.filter(sample(UINT32_MAX,true),3).cancelled);
    assert(!delivery.filter(sample(0),3).cancelled);
    espocket::ShellGestureState state;
    assert(espocket::native_pointer_access_epoch(state,true,true));
    assert(!espocket::native_pointer_access_epoch(state,false,true));
    assert(!espocket::native_pointer_access_epoch(state,true,false));
    for(auto* flag:{&state.modal_active,&state.keyboard_active,&state.consumed,&state.pointer_cancel_pending}){
        flag->store(true);assert(!espocket::native_pointer_access_epoch(state,true,true));flag->store(false);
    }
    state.surface.store(espocket::ShellSurface::QuickSettings);
    assert(!espocket::native_pointer_access_epoch(state,true,true));
    state.surface.store(espocket::ShellSurface::WatchFace);
    auto epoch=*espocket::native_pointer_access_epoch(state,true,true);
    espocket::reset_shell_gesture(state,true);assert(state.input_epoch.load()!=epoch);
    state.consumed.store(false);
    espocket::process_shell_gesture(state,{.phase=espocket::ShellGesturePhase::Press},{.app_visible=true});
    espocket::process_shell_gesture(state,{.phase=espocket::ShellGesturePhase::Pressing,
        .direction=espocket::ShellGestureDirection::Down,.start_y=1,.distance_px=100001},{.app_visible=true});
    assert(!espocket::native_pointer_access_epoch(state,true,true));
    assert(state.input_epoch.load()!=epoch);
}
''')
            shell = ROOT / 'firmware/components/shell_circular'
            binary = work / 'test'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread',
                            '-I', str(gui / 'include'), '-I', str(shell / 'include'),
                            str(source), str(shell / 'src/shell_gesture.cpp'), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=10)

    def test_existing_pointer_manager_publishes_assigned_cache(self):
        with tempfile.TemporaryDirectory(prefix='native-pointer-cache-') as directory:
            work = Path(directory)
            component = 'espressif__brookesia_gui_lvgl'
            lvgl = prepare(ROOT / 'firmware/managed_components' / component,
                           ROOT / 'firmware/patches' / component / '0.8.5/manifest.json', work / 'lvgl')
            text = (lvgl / 'src/port/private/multi_touch_pointer.hpp').read_text()
            getter = text[text.index('    NativePointerFrame cached_pointer_frame() const'):
                          text.index('    static size_t resolve_input_count(')]
            slot = text[text.index('    struct Slot {'):text.index('    static constexpr int32_t NEAREST_MATCH_DISTANCE_PX')]
            assignment = text[text.index('    void assign_snapshot_points('):
                              text.index('#if LVGL_VERSION_MAJOR >= 9 && LV_USE_GESTURE_RECOGNITION\n    void update_gesture_recognizers')]
            # Stub only boundary structs; execute actual slot assignment and cache projection.
            source = work / 'test.cpp'
            source.write_text(r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <limits>
#include <optional>
#include <vector>
using lv_coord_t=int32_t;
struct lv_point_t {int32_t x=0,y=0;};
struct NativePointerPoint {int32_t x,y;uint8_t track_id;};
struct NativePointerFrame {std::vector<NativePointerPoint> points;uint32_t sequence=0;uint64_t updated_at_ms=0;bool valid=false,cancelled=true;};
namespace service {struct Display {struct TouchPoint {int16_t x,y;uint8_t track_id=0;};};}
struct Manager {
 static constexpr size_t MAX_INPUT_COUNT=5,INVALID_SLOT=5;
 static constexpr int32_t NEAREST_MATCH_DISTANCE_PX=96;
''' + slot + getter + assignment + r'''
 std::array<Slot,MAX_INPUT_COUNT> slots_{};size_t input_count_=5;uint8_t next_synthetic_track_id_=1;
 bool sample_valid_=true,has_snapshot_sequence_=true;
 struct Snapshot {uint32_t sequence=8;uint64_t updated_at_ms=100;bool valid=true;}snapshot_;
};
int main(){
 Manager m;m.assign_snapshot_points({{100,100,1},{300,300,2}});
 auto f=m.cached_pointer_frame();assert(f.valid && f.sequence==8 && f.updated_at_ms==100 && f.points.size()==2);
 m.assign_snapshot_points({{320,310,2}});f=m.cached_pointer_frame();assert(f.points.size()==1 && f.points[0].track_id==2);
 assert(f.points[0].x==320 && f.points[0].y==310);
 m.assign_snapshot_points({});assert(m.cached_pointer_frame().points.empty());
 m.sample_valid_=false;assert(!m.cached_pointer_frame().valid);
 m.sample_valid_=true;m.snapshot_.valid=false;assert(!m.cached_pointer_frame().valid);
}
''')
            binary = work / 'test'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(source), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=10)
            self.assertNotIn('get_touch_snapshot', getter)
