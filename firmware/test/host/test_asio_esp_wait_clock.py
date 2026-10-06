"""Exercise Asio's actual ESP timed-wait method with a default-clock pthread condition."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare
SOURCE = ROOT / 'firmware/managed_components/espressif__esp-boost'
MANIFEST = ROOT / 'firmware/patches/espressif__esp-boost/0.6.0/manifest.json'


def exercise(source, directory):
    text = (source / 'src/boost/asio/detail/posix_event.hpp').read_text()
    start = text.index('  template <typename Lock>\n  bool wait_for_usec(')
    method = text[start:text.index('\nprivate:', start)]
    code = r'''
#include <cassert>
#include <chrono>
#include <cstddef>
#include <pthread.h>
#include <thread>
// Exercise the ESP branch on the host, with ESP's default realtime cond clock.
#undef __MACH__
#undef __APPLE__
#define ESP_PLATFORM 1
#define BOOST_ASIO_ASSERT assert
struct Mutex { pthread_mutex_t mutex_ = PTHREAD_MUTEX_INITIALIZER; };
struct Lock {
    Mutex &m;
    Lock(Mutex &m):m(m) { pthread_mutex_lock(&m.mutex_); }
    ~Lock() { pthread_mutex_unlock(&m.mutex_); }
    bool locked() { return true; }
    Mutex &mutex() { return m; }
};
struct Event {
    pthread_cond_t cond_ = PTHREAD_COND_INITIALIZER;
    std::size_t state_ = 0;
''' + method + r'''
};
int main() {
    using namespace std::chrono_literals;
    Event event;
    Mutex mutex;
    {
        Lock lock(mutex);
        const auto start = std::chrono::steady_clock::now();
        assert(!event.wait_for_usec(lock, 20000));
        const auto elapsed = std::chrono::steady_clock::now() - start;
        assert(elapsed >= 10ms && elapsed < 200ms);
    }
    std::thread signal([&] {
        std::this_thread::sleep_for(5ms);
        Lock lock(mutex);
        event.state_ |= 1;
        pthread_cond_signal(&event.cond_);
    });
    {
        Lock lock(mutex);
        assert(event.wait_for_usec(lock, 100000));
    }
    signal.join();
    pthread_cond_destroy(&event.cond_);
    pthread_mutex_destroy(&mutex.mutex_);
}
'''
    directory = Path(directory)
    cpp, binary = directory / 'clock.cpp', directory / 'clock'
    cpp.write_text(code)
    subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread',
                    str(cpp), '-o', str(binary)], check=True)
    return subprocess.run([str(binary)], capture_output=True, timeout=10)


class AsioEspWaitClockTest(unittest.TestCase):
    def test_default_clock_timeout_and_post_wakeup(self):
        with tempfile.TemporaryDirectory(prefix='espocket-asio-clock-') as d:
            self.assertNotEqual(exercise(SOURCE, d).returncode, 0)
            patched = prepare(SOURCE, MANIFEST, Path(d) / 'patched')
            result = exercise(patched, d)
            self.assertEqual(result.returncode, 0, result.stderr)
