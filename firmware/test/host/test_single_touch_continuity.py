"""Exercise actual LVGL pointer assignment across sparse, fast touch samples."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare

SOURCE = ROOT / 'firmware/managed_components/espressif__brookesia_gui_lvgl'
MANIFEST = ROOT / 'firmware/patches/espressif__brookesia_gui_lvgl/0.8.5/manifest.json'
HEADER = r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <limits>
#include <vector>
using lv_coord_t = int32_t;
struct lv_point_t { int32_t x = 0, y = 0; };
namespace service { struct Display { struct TouchPoint { int16_t x, y; uint8_t track_id = 0; }; }; }
class Manager {
public:
static constexpr size_t MAX_INPUT_COUNT = 5, INVALID_SLOT = 5;
static constexpr int32_t NEAREST_MATCH_DISTANCE_PX = 96;
'''
DRIVER = r'''
std::array<Slot, MAX_INPUT_COUNT> slots_{};
size_t input_count_ = 5;
uint8_t next_synthetic_track_id_ = 1;
};
int main() {
    Manager manager;
    manager.assign_snapshot_points({{233, 400}});
    auto track = manager.slots_[0].track_id;
    manager.assign_snapshot_points({{233, 150}});
    if (!manager.slots_[0].active || manager.slots_[0].release_pending) return 1;
    assert(manager.slots_[0].point.y == 150 && manager.slots_[0].track_id == track);
    assert(!manager.slots_[1].allocated());
    manager.assign_snapshot_points({});
    assert(!manager.slots_[0].active && manager.slots_[0].release_pending);
    manager.slots_ = {};
    manager.assign_snapshot_points({{100, 100, 1}, {300, 300, 2}});
    manager.assign_snapshot_points({{330, 330, 2}, {50, 50, 1}});
    assert(manager.slots_[0].track_id == 1 && manager.slots_[0].point.x == 50);
    assert(manager.slots_[1].track_id == 2 && manager.slots_[1].point.x == 330);
    manager.slots_ = {};
    manager.assign_snapshot_points({{100, 100}, {300, 300}});
    manager.assign_snapshot_points({{120, 120}, {320, 320}});
    assert(manager.slots_[0].active && manager.slots_[1].active);
    return 0;
}
'''


def build(component, directory):
    source = (component / 'src/port/private/multi_touch_pointer.hpp').read_text()
    slot = source[source.index('    struct Slot {'):source.index('    static constexpr int32_t NEAREST_MATCH_DISTANCE_PX')]
    methods = source[source.index('    void assign_snapshot_points('):source.index('#if LVGL_VERSION_MAJOR >= 9 && LV_USE_GESTURE_RECOGNITION\n    void update_gesture_recognizers')]
    directory.mkdir()
    harness = directory / 'probe.cpp'
    harness.write_text(HEADER + slot + methods + DRIVER)
    binary = directory / 'probe'
    subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(harness), '-o', str(binary)], check=True)
    return binary


class SingleTouchContinuityTest(unittest.TestCase):
    def test_fast_single_touch_keeps_track_without_breaking_multitouch(self):
        with tempfile.TemporaryDirectory(prefix='espocket-touch-track-') as temporary:
            directory = Path(temporary)
            original = build(SOURCE, directory / 'original')
            self.assertEqual(subprocess.run([str(original)], timeout=5).returncode, 1)
            patched = prepare(SOURCE, MANIFEST, directory / 'component')
            candidate = build(patched, directory / 'patched')
            self.assertEqual(subprocess.run([str(candidate)], timeout=5).returncode, 0)
