"""Execute the locked Core's actual Runtime stop branch with failed on_stop."""
import os
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
CORE = Path(os.environ.get('ESPOCKET_CORE_SOURCE', str(ROOT / 'firmware/managed_components/espressif__brookesia_system_core')))


def runtime_stop_branch(core):
    text = (core / 'src/app/manager.cpp').read_text()
    start = text.index('        auto heap_before_lifecycle = heap_trace::capture();', text.index('System::stop_app(AppId app_id)'))
    end = text.index('        record.runtime_started = false;', start)
    return text[start:end]


class CoreFailedStopTest(unittest.TestCase):
    def test_failed_lifecycle_still_releases_runtime_resources(self):
        sys.path.insert(0, str(ROOT / 'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='espocket-core-copy-') as directory:
            patched = prepare(CORE, ROOT / 'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json',
                              Path(directory) / 'patched')
            original = self.exercise(CORE)
            self.assertNotEqual(original.returncode, 0)
            self.assertIn('skipped Runtime cleanup', original.stderr)
            fixed = self.exercise(patched)
            self.assertEqual(fixed.returncode, 0, fixed.stderr)

    def exercise(self, core):
        harness = r'''
#include <cassert>
#include <expected>
#include <memory>
#include <optional>
#include <string>
#include <iostream>
namespace heap_trace { inline int capture() { return 0; } template<class... T> void log(T&&...) {} }
constexpr const char* LIFECYCLE_ON_STOP = "on_stop";
struct Runtime { int stops = 0; bool backend_failure = false;
    std::expected<void, std::string> stop_app(int) { ++stops; if (backend_failure) return std::unexpected("backend_error"); return {}; }
};
struct Record { struct { struct { std::string id = "hostile"; } manifest; } info;
    std::optional<int> runtime_app_id = 7;
};
struct Impl { std::shared_ptr<Runtime> runtime_ = std::make_shared<Runtime>(); bool lifecycle_failure = false;
    std::expected<void, std::string> call_runtime_lifecycle(Record&, const char*) {
        if (lifecycle_failure) return std::unexpected("lifecycle_error"); return {};
    }
};
std::expected<void, std::string> exercise(Impl* impl_, Record& record) {
    std::expected<void, std::string> stop_result;
''' + runtime_stop_branch(core) + r'''
    return stop_result;
}
int main() {
    for (bool lifecycle_failure : {false, true}) for (bool backend_failure : {false, true}) {
        Impl impl; Record record;
        impl.lifecycle_failure = lifecycle_failure; impl.runtime_->backend_failure = backend_failure;
        auto result = exercise(&impl, record);
        if (impl.runtime_->stops != 1) { std::cerr << "FAIL: failed on_stop skipped Runtime cleanup\n"; return 1; }
        assert(bool(result) == (!lifecycle_failure && !backend_failure));
        if (lifecycle_failure) assert(result.error() == "lifecycle_error");
        else if (backend_failure) assert(result.error() == "backend_error");
    }
}
'''
        with tempfile.TemporaryDirectory(prefix='espocket-core-stop-') as directory:
            source = Path(directory) / 'test.cpp'
            binary = Path(directory) / 'test'
            source.write_text(harness)
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(source), '-o', str(binary)], check=True)
            return subprocess.run([str(binary)], text=True, capture_output=True)
