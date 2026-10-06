"""GUI root parse allocation failures must return to the waiting Core owner."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


def exercise(component, directory):
    source = (component / 'src/runtime.cpp').read_text()
    begin = source.index('std::expected<DocumentId, std::string> Runtime::load_file(')
    method = source[begin:source.index('std::expected<void, std::string> Runtime::load_theme(', begin)]
    harness = r'''
#include <cassert>
#include <chrono>
#include <expected>
#include <memory>
#include <new>
#include <string>
#include <string_view>
#include <vector>
#define GUI_INTERFACE_PROFILE_LOGI(...)
using RuntimeProfileClock = std::chrono::steady_clock;
auto runtime_profile_elapsed_ms(auto start, auto end) { return (end - start).count(); }
struct Environment {};
struct Document { std::vector<int> images, screens, templates; };
struct ParsedDocument { Document document; std::vector<std::string> dependency_files; };
struct DocumentId { unsigned identity = 1; unsigned value() const { return identity; } };
bool allocation_fails = true, parse_fails = false;
std::expected<ParsedDocument, std::string> parse_document_file_with_metadata(std::string_view, Environment) {
    if (allocation_fails) throw std::bad_alloc();
    if (parse_fails) return std::unexpected("invalid root");
    return ParsedDocument{};
}
struct Runtime {
    struct Impl {
        unsigned loads = 0;
        Environment make_parse_environment(Environment environment) { return environment; }
        std::expected<DocumentId, std::string> load(std::string_view, Document, Environment,
                                                  bool, std::vector<std::string>) {
            ++loads;
            return DocumentId{};
        }
    };
    std::unique_ptr<Impl> impl_ = std::make_unique<Impl>();
    std::expected<DocumentId, std::string> load_file(std::string_view, const Environment &);
};
''' + method + r'''
int main() {
    Runtime runtime;
    try {
        auto failed = runtime.load_file("weather/root.json", {});
        assert(!failed && failed.error() == "GUI out of memory");
        assert(runtime.impl_->loads == 0);
    } catch (const std::bad_alloc &) {
        return 1;
    }
    allocation_fails = false;
    parse_fails = true;
    auto invalid = runtime.load_file("weather/root.json", {});
    assert(!invalid && invalid.error() == "invalid root");
    assert(runtime.impl_->loads == 0);
    parse_fails = false;
    assert(runtime.load_file("weather/root.json", {}));
    assert(runtime.impl_->loads == 1);
}
'''
    source_path = Path(directory) / 'probe.cpp'
    binary = Path(directory) / 'probe'
    source_path.write_text(harness)
    subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(source_path),
                    '-o', str(binary)], check=True)
    return subprocess.run([str(binary)], timeout=5, check=False).returncode


class GuiRootAllocationFailureTest(unittest.TestCase):
    def test_failed_parse_returns_error_and_next_load_can_succeed(self):
        upstream = ROOT / 'firmware/managed_components/espressif__brookesia_gui_interface'
        manifest = ROOT / 'firmware/patches/espressif__brookesia_gui_interface/0.8.2/manifest.json'
        with tempfile.TemporaryDirectory(prefix='espocket-root-allocation-') as directory:
            self.assertNotEqual(exercise(upstream, directory), 0)
            patched = prepare(upstream, manifest, Path(directory) / 'patched')
            self.assertEqual(exercise(patched, directory), 0)
