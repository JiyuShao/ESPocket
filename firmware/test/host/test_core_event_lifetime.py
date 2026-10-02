"""Execute the real Core event queue callback across unsubscribe/stop/restart."""
import os
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / 'firmware/managed_components/espressif__brookesia_system_core'

class CoreEventLifetimeTest(unittest.TestCase):
    def test_revoked_subscription_cannot_deliver_already_queued_event(self):
        sys.path.insert(0, str(ROOT / 'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='espocket-core-copy-') as directory:
            patched = prepare(CORE, ROOT / 'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json',
                              Path(directory) / 'patched')
            original = self.exercise(CORE)
            self.assertNotEqual(original.returncode, 0)
            self.assertIn('revoked subscription delivered queued event', original.stderr)
            fixed = self.exercise(patched)
            self.assertEqual(fixed.returncode, 0, fixed.stderr)

    def exercise(self, core):
        text = (core / 'src/system/lifecycle.cpp').read_text()
        start = text.index('    auto event_dispatcher = [this](')
        end = text.index('    impl_->host_bridge_', start)
        callback = text[start:end]
        token_arg = ', active' if 'event_active' in callback else ''
        harness = r'''
#include <atomic>
#include <expected>
#include <functional>
#include <map>
#include <memory>
#include <string>
#include <vector>
#include <iostream>
namespace runtime { using AppId = unsigned; }
using AppId = unsigned;
constexpr int SYSTEM_APP_INPUT_TASK_GROUP = 0;
#define BROOKESIA_LOGW(...)
struct Impl { std::map<unsigned, unsigned> runtime_to_app_{{7, 1}};
    std::vector<std::function<void()>> queue; int delivered = 0;
    std::expected<void, std::string> post_task(int, std::function<void()> task) { queue.push_back(task); return {}; }
    std::expected<void, std::string> dispatch_event(unsigned, std::string, std::string, std::string) { ++delivered; return {}; }
};
struct System { std::unique_ptr<Impl> impl_ = std::make_unique<Impl>();
    int exercise() {
''' + callback + r'''
    auto active = std::make_shared<std::atomic<bool>>(true);
    auto result = event_dispatcher(7, "SystemCore", "KeyboardClosed", "{}"''' + token_arg + r''');
    if (!result || impl_->queue.size() != 1) return 2;
    active->store(false); // stop/unsubscribe while event is queued
    impl_->queue.front()();
    if (impl_->delivered) { std::cerr << "FAIL: revoked subscription delivered queued event\n"; return 1; }
    impl_->queue.clear();
    active = std::make_shared<std::atomic<bool>>(true); // same App ID, new instance/subscription
    result = event_dispatcher(7, "Display", "Changed", "{}"''' + token_arg + r''');
    if (!result || impl_->queue.size() != 1) return 3;
    impl_->queue.front()();
    return impl_->delivered == 1 ? 0 : 4;
}};
int main() { System system; return system.exercise(); }
'''
        with tempfile.TemporaryDirectory(prefix='espocket-core-queue-') as directory:
            source = Path(directory) / 'test.cpp'; source.write_text(harness)
            binary = Path(directory) / 'test'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(source), '-o', str(binary)], check=True)
            return subprocess.run([str(binary)], text=True, capture_output=True)
