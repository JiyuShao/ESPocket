"""Exercise the real worker dispatch block with a continuously ready queue."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare

SOURCE = ROOT / 'firmware/managed_components/espressif__brookesia_lib_utils'
MANIFEST = ROOT / 'firmware/patches/espressif__brookesia_lib_utils/0.8.2/manifest.json'


def exercise(source, directory):
    text = (source / 'src/task_scheduler.cpp').read_text()
    start = text.index('size_t executed = io_context_->')
    block = text[start:text.index('} catch (const boost::thread_interrupted', start)]
    code = r'''
#include <cassert>
#include <cstddef>
#include <chrono>
int idle_windows = 0, tasks = 0, largest_batch = 0, blocking_waits = 0;
namespace boost {
namespace chrono { using milliseconds = std::chrono::milliseconds; }
namespace this_thread { void sleep_for(std::chrono::milliseconds delay) {
    assert(delay.count() > 0); ++idle_windows;
} }
}
struct Queue {
    bool ready = true;
    size_t poll() { if (!ready) return 0; tasks += 32; largest_batch = 32; return 32; }
    size_t poll_one() { if (!ready) return 0; ++tasks; largest_batch = 1; return 1; }
    size_t run_one_for(std::chrono::milliseconds delay) {
        assert(delay.count() > 0);
        if (!ready) { ++blocking_waits; return 0; }
        ++tasks; largest_batch = 1; return 1;
    }
};
int main() {
    Queue queue; auto *io_context_ = &queue; int poll_interval_ms = 10;
    for (int iteration = 0; iteration < 8; ++iteration) {
''' + block + r'''
    }
    assert(idle_windows == 8); // Busy work must let Idle run too.
    assert(tasks == 8 && largest_batch == 1); // Bound dispatch before sleeping.
    queue.ready = false;
    {
''' + block + r'''
    }
    assert(idle_windows == 8 && blocking_waits == 1 && tasks == 8);
}
'''
    cpp = Path(directory) / 'fairness.cpp'
    binary = Path(directory) / 'fairness'
    cpp.write_text(code)
    subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(cpp), '-o', str(binary)], check=True)
    return subprocess.run([str(binary)], capture_output=True).returncode


class SchedulerFairnessTest(unittest.TestCase):
    def test_continuous_queue_allows_idle_and_empty_queue_waits(self):
        with tempfile.TemporaryDirectory() as directory:
            # Baseline proves this regression detects the actual busy-loop defect.
            self.assertNotEqual(exercise(SOURCE, directory), 0)
            patched = prepare(SOURCE, MANIFEST, Path(directory) / 'patched')
            self.assertEqual(exercise(patched, directory), 0)


if __name__ == '__main__':
    unittest.main()
