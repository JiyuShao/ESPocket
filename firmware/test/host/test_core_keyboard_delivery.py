"""Execute Core's real event delivery method across two App owners."""
import os
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / 'firmware/managed_components/espressif__brookesia_system_core'
BOOST = ROOT / 'firmware/managed_components/espressif__esp-boost/src'


def delivery_method(core):
    text = (core / 'src/app/manager.cpp').read_text()
    start = text.index('std::expected<void, std::string> System::Impl::dispatch_event(')
    end = text.index('\n\n\nstd::expected<AppId', start)
    return text[start:end]


class CoreKeyboardDeliveryTest(unittest.TestCase):
    def test_result_is_owned_and_stopped_instances_do_not_receive_events(self):
        sys.path.insert(0, str(ROOT / 'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='espocket-core-copy-') as directory:
            patched = prepare(CORE, ROOT / 'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json',
                              Path(directory) / 'patched')
            original = self.exercise(CORE)
            self.assertNotEqual(original.returncode, 0)
            self.assertIn('keyboard Text delivered to another App', original.stderr)
            fixed = self.exercise(patched)
            self.assertEqual(fixed.returncode, 0, fixed.stderr)

    def exercise(self, core):
        harness = r'''
#include <boost/json.hpp>
#include <cassert>
#include <expected>
#include <string>
#include <vector>
#include <map>
#include <iostream>
using AppId = unsigned;
enum class AppKind { Native, Runtime };
enum class AppState { Running, Paused, Stopped, Error, Stopping, Installed };
constexpr const char* LIFECYCLE_ON_EVENT = "on_event";
#define BROOKESIA_DESCRIBE_TO_STR(value) "KeyboardClosed"
struct SystemCoreHelper { enum class EventId { KeyboardClosed }; static std::string get_name() { return "SystemCore"; } };
struct Record { struct { struct { AppKind kind = AppKind::Runtime; } manifest;
    AppState state = AppState::Running; } info; bool runtime_started = true;
};
class System { public: struct Impl {
    std::map<AppId, Record> records{{1, {}}, {2, {}}}; int delivered = 0;
    std::expected<Record*, std::string> get_record(AppId id) {
        auto it = records.find(id); if(it == records.end()) return std::unexpected("not_found"); return &it->second;
    }
    std::expected<void, std::string> call_runtime_lifecycle(Record&, const char*, std::vector<std::string>) { ++delivered; return {}; }
    std::expected<void, std::string> dispatch_event(AppId, std::string, std::string, std::string);
}; };
''' + delivery_method(core) + r'''
int main() {
    System::Impl impl;
    const std::string result = R"({"AppId":1.0,"RequestId":4,"Confirmed":true,"Text":"PRIVATE_TEST_VALUE"})";
    impl.dispatch_event(2, "SystemCore", "KeyboardClosed", result);
    if (impl.delivered != 0) { std::cerr << "FAIL: keyboard Text delivered to another App\n"; return 1; }
    for (const std::string malformed : {"{}", "not-json", "[]", "{\"AppId\":\"1\"}", "{\"AppId\":1.5}"})
        impl.dispatch_event(1, "SystemCore", "KeyboardClosed", malformed);
    assert(impl.delivered == 0);
    assert(impl.dispatch_event(1, "SystemCore", "KeyboardClosed", result));
    assert(impl.delivered == 1);
    impl.dispatch_event(2, "Display", "BrightnessChanged", "{}");
    assert(impl.delivered == 2); // non-private public events remain available
    for (AppState state : {AppState::Stopped, AppState::Error, AppState::Stopping, AppState::Installed}) {
        impl.records[1].info.state = state;
        impl.dispatch_event(1, "SystemCore", "KeyboardClosed", result);
        assert(impl.delivered == 2);
    }
    impl.records[1].info.state = AppState::Running;
    impl.records[1].runtime_started = false;
    impl.dispatch_event(1, "SystemCore", "KeyboardClosed", result);
    assert(impl.delivered == 2);
}
'''
        with tempfile.TemporaryDirectory(prefix='espocket-core-keyboard-') as directory:
            source = Path(directory) / 'test.cpp'; source.write_text(harness)
            boost = Path(directory) / 'boost.cpp'; boost.write_text('#include <boost/json/src.hpp>\n')
            binary = Path(directory) / 'test'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-DBOOST_NO_USER_CONFIG',
                            '-I', str(BOOST), str(source), str(boost), '-o', str(binary)], check=True)
            return subprocess.run([str(binary)], text=True, capture_output=True)
