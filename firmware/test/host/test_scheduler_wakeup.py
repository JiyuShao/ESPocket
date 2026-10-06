"""A task posted to an idle real Asio worker must wake it before the poll deadline."""
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
BOOST = ROOT / 'firmware/managed_components/espressif__esp-boost/src'


def exercise(source, directory):
    text = (source / 'src/task_scheduler.cpp').read_text()
    start = text.index('size_t executed = io_context_->')
    block = text[start:text.index('} catch (const boost::thread_interrupted', start)]
    code = r'''
#include <boost/asio.hpp>
#include <atomic>
#include <chrono>
#include <future>
#include <thread>
#include <cassert>
namespace boost {
namespace chrono { using milliseconds = std::chrono::milliseconds; }
namespace this_thread { void sleep_for(std::chrono::milliseconds d) { std::this_thread::sleep_for(d); } }
}
int main() {
    using namespace std::chrono_literals;
    boost::asio::io_context context;
    auto *io_context_ = &context;
    auto work = boost::asio::make_work_guard(context);
    int poll_interval_ms = 200;
    std::promise<void> timer_dispatched;
    auto timer_ready = timer_dispatched.get_future();
    boost::asio::steady_timer timer(context, 45ms);
    timer.async_wait([&](const boost::system::error_code &error) {
        if (!error) timer_dispatched.set_value();
    });
    std::atomic<bool> entered{false};
    std::thread worker([&] {
        entered = true;
        while (!context.stopped()) {
''' + block + r'''
        }
    });
    while (!entered) std::this_thread::yield();
    std::this_thread::sleep_for(20ms); // Put the worker inside its idle wait.
    std::promise<void> dispatched;
    auto ready = dispatched.get_future();
    boost::asio::post(context, [&] { dispatched.set_value(); });
    const bool woke = ready.wait_for(80ms) == std::future_status::ready;
    const bool timer_woke = timer_ready.wait_for(80ms) == std::future_status::ready;
    context.stop();
    worker.join();
    assert(woke); // Deadline is independent of the configured idle poll interval.
    assert(timer_woke);
}
'''
    directory = Path(directory)
    cpp, binary = directory / 'wakeup.cpp', directory / 'wakeup'
    cpp.write_text(code)
    subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread',
                    '-DBOOST_NO_USER_CONFIG', '-I', str(BOOST), str(cpp), '-o', str(binary)], check=True)
    return subprocess.run([str(binary)], capture_output=True, timeout=10)


class SchedulerWakeupTest(unittest.TestCase):
    def test_idle_worker_wakes_on_post(self):
        with tempfile.TemporaryDirectory(prefix='espocket-worker-wakeup-') as d:
            self.assertNotEqual(exercise(SOURCE, d).returncode, 0)
            patched = prepare(SOURCE, MANIFEST, Path(d) / 'patched')
            result = exercise(patched, d)
            self.assertEqual(result.returncode, 0, result.stderr)
