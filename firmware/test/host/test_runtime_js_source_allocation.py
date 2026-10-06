"""Run actual QuickJS file-loader bodies with budget and cleanup fault injection."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
sys.path.insert(0, str(Path(__file__).parent))
from prepare_patched_component import prepare
from test_gui_image_read_allocation import HARNESS as STORAGE_HARNESS

SOURCE = ROOT / 'firmware/managed_components/espressif__brookesia_runtime_js'
MANIFEST = ROOT / 'firmware/patches/espressif__brookesia_runtime_js/0.8.3/manifest.json'
HARNESS = STORAGE_HARNESS.replace(
    'fs_stat(const std::string &)', 'fs_stat(const std::string &, uint32_t = 0)').replace(
    'fs_read_text(const std::string &)', 'fs_read_text(const std::string &, uint32_t = 0)').replace(
    'const service::RawBuffer &buffer)', 'const service::RawBuffer &buffer, uint32_t = 0)') + r'''
#include <memory>
#include <stdexcept>
namespace service::helper { using Storage = ::StorageHelper; }
constexpr uint32_t STORAGE_FS_TIMEOUT_MS = 5000;
struct JSContext {};
bool js_allocation_fails = false;
void *js_malloc(JSContext *, size_t size) {
    if (js_allocation_fails) return nullptr;
    try { return new uint8_t[size]; } catch (const std::bad_alloc &) { return nullptr; }
}
void js_free(JSContext *, void *pointer) { delete[] static_cast<uint8_t *>(pointer); }
'''
DRIVER = r'''
int main(int argc, char **argv) {
    assert(argc == 2);
    for (size_t index = 0; index < payload.size(); ++index) payload[index] = index % 256;
    JSContext context;
    size_t length = 99;
    const auto load = [&] { return brookesia_js_load_file(&context, &length, "module.js"); };
    if (std::string_view(argv[1]) == "module" || std::string_view(argv[1]) == "entry") {
        budget_bytes = payload.size() + 4096;
        try {
            if (std::string_view(argv[1]) == "module") {
                auto *source = load();
                budget_bytes = 0;
                if (!source) return 1;
                assert(length == payload.size() && source[length] == 0);
                assert(std::equal(source, source + length, payload.begin()));
                js_free(&context, source);
            } else {
                auto source = read_all("entry.js");
                budget_bytes = 0;
                if (!source) return 1;
                assert(source->size() == payload.size());
                assert(std::memcmp(source->data(), payload.data(), payload.size()) == 0);
            }
            assert(live_bytes == 0);
            return 0;
        } catch (const std::bad_alloc &) {
            budget_bytes = 0;
            return 1;
        }
    }
    const auto rejected = [&] {
        length = 99;
        assert(load() == nullptr && length == 0 && live_bytes == 0);
    };
    stat_error = true;
    rejected();
    assert(!read_all("entry.js"));
    stat_error = false;
    missing = true;
    rejected();
    missing = false;
    directory = true;
    rejected();
    directory = false;
    file_size = std::numeric_limits<size_t>::max();
    rejected();
    assert(!read_all("entry.js") && read_calls == 0);
    file_size = payload.size();
    js_allocation_fails = true;
    rejected();
    js_allocation_fails = false;
    for (unsigned repeat = 0; repeat < 20; ++repeat) {
        read_error = true;
        rejected();
        assert(!read_all("entry.js"));
        read_error = false;
        short_read = true;
        rejected();
        assert(!read_all("entry.js"));
        short_read = false;
    }
    file_size = 0;
    auto *empty = load();
    assert(empty && length == 0 && empty[0] == 0);
    js_free(&context, empty);
    assert(live_bytes == 0 && read_all("entry.js")->empty());
    return 0;
}
'''


def build(component, directory):
    source = (component / 'src/backend.cpp').read_text()
    begin = source.index('std::expected<std::string, std::string> read_all(')
    end = source.index('/** Custom module loader', begin)
    directory.mkdir()
    harness = directory / 'probe.cpp'
    harness.write_text(HARNESS + source[begin:end] + DRIVER)
    binary = directory / 'probe'
    subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(harness),
                    '-o', str(binary)], check=True, timeout=30)
    return binary


class RuntimeJsSourceAllocationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='espocket-js-source-')
        directory = Path(cls.temporary.name)
        prepared = prepare(SOURCE, MANIFEST, directory / 'component')
        cls.original = build(SOURCE, directory / 'original')
        cls.patched = build(prepared, directory / 'patched')

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_original_module_and_entry_exceed_budget(self):
        for mode in ('module', 'entry'):
            with self.subTest(mode=mode):
                self.assertEqual(subprocess.run([str(self.original), mode], timeout=5).returncode, 1)

    def test_module_and_entry_fit_single_source_budget(self):
        for mode in ('module', 'entry'):
            with self.subTest(mode=mode):
                self.assertEqual(subprocess.run([str(self.patched), mode], timeout=5).returncode, 0)

    def test_failed_module_loads_free_quickjs_buffer(self):
        self.assertEqual(subprocess.run([str(self.patched), 'edges'], timeout=5).returncode, 0)


if __name__ == '__main__':
    unittest.main()
