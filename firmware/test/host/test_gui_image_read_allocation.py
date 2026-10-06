"""Exercise the actual image reader under a budget that fits one binary buffer."""
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
HARNESS = r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <expected>
#include <limits>
#include <new>
#include <string>
#include <string_view>
#include <vector>
struct alignas(std::max_align_t) Allocation { size_t size; };
size_t live_bytes = 0, budget_bytes = 0;
void *operator new(size_t size) {
    if (budget_bytes && (live_bytes > budget_bytes || size > budget_bytes - live_bytes))
        throw std::bad_alloc();
    auto *block = static_cast<Allocation *>(std::malloc(sizeof(Allocation) + size));
    if (!block) throw std::bad_alloc();
    block->size = size;
    live_bytes += size;
    return block + 1;
}
void operator delete(void *pointer) noexcept {
    if (!pointer) return;
    auto *block = static_cast<Allocation *>(pointer) - 1;
    live_bytes -= block->size;
    std::free(block);
}
void *operator new[](size_t size) { return ::operator new(size); }
void operator delete[](void *pointer) noexcept { ::operator delete(pointer); }
void operator delete(void *pointer, size_t) noexcept { ::operator delete(pointer); }
void operator delete[](void *pointer, size_t) noexcept { ::operator delete(pointer); }
namespace service {
struct RawBuffer {
    uint8_t *data;
    size_t size;
    RawBuffer(void *pointer, size_t length) : data(static_cast<uint8_t *>(pointer)), size(length) {}
};
}
std::array<uint8_t, 95244> payload;
uint64_t file_size = payload.size();
bool stat_error = false, missing = false, directory = false, read_error = false, short_read = false;
unsigned read_calls = 0;
struct StorageHelper {
    enum class FileType { File, Directory };
    struct FileInfo { uint64_t size; bool exists; FileType type; };
    static std::expected<FileInfo, std::string> fs_stat(const std::string &) {
        if (stat_error) return std::unexpected("stat failed");
        return FileInfo{file_size, !missing, directory ? FileType::Directory : FileType::File};
    }
    static std::expected<std::string, std::string> fs_read_text(const std::string &) {
        return std::string(reinterpret_cast<const char *>(payload.data()), payload.size());
    }
    static std::expected<size_t, std::string> fs_read(const std::string &, const service::RawBuffer &buffer) {
        ++read_calls;
        if (read_error) return std::unexpected("read failed");
        assert(buffer.size <= payload.size());
        const size_t count = short_read ? buffer.size - 1 : buffer.size;
        std::memcpy(buffer.data, payload.data(), count);
        return count;
    }
};
'''
DRIVER = r'''
int main(int argc, char **argv) {
    assert(argc == 2);
    for (size_t index = 0; index < payload.size(); ++index) payload[index] = index % 256;
    if (std::string_view(argv[1]) == "budget") {
        budget_bytes = payload.size() + 4096;
        try {
            auto data = read_storage_file_bytes("image.bin", "LVGL bin");
            budget_bytes = 0;
            assert(data && data->size() == payload.size());
            assert(std::equal(data->begin(), data->end(), payload.begin()));
            return 0;
        } catch (const std::bad_alloc &) {
            budget_bytes = 0;
            return 1;
        }
    }
    const auto read = [] { return read_storage_file_bytes("image.bin", "LVGL bin"); };
    stat_error = true;
    assert(!read() && read().error().find("stat failed") != std::string::npos);
    stat_error = false;
    missing = true;
    assert(!read());
    missing = false;
    directory = true;
    assert(!read());
    directory = false;
    file_size = uint64_t{std::numeric_limits<uint32_t>::max()} + 1;
    assert(!read());
    assert(read_calls == 0);
    file_size = 0;
    auto empty = read();
    assert(empty && empty->empty() && read_calls == 0);
    file_size = payload.size();
    read_error = true;
    assert(!read() && read().error().find("read failed") != std::string::npos);
    read_error = false;
    short_read = true;
    assert(!read() && read().error().find("size mismatch") != std::string::npos);
    short_read = false;
    auto full = read();
    assert(full && std::equal(full->begin(), full->end(), payload.begin()));
    return 0;
}
'''


def build(component, directory):
    source = (component / 'src/props_image.cpp').read_text()
    begin = source.index('std::expected<std::vector<uint8_t>, std::string> read_storage_file_bytes(')
    end = source.index('std::expected<std::shared_ptr<BinaryImageSource>', begin)
    directory.mkdir()
    harness = directory / 'probe.cpp'
    harness.write_text(HARNESS + source[begin:end] + DRIVER)
    binary = directory / 'probe'
    subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(harness),
                    '-o', str(binary)], check=True, timeout=30)
    return binary


class GuiImageReadAllocationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='espocket-image-read-')
        directory = Path(cls.temporary.name)
        prepared = prepare(SOURCE, MANIFEST, directory / 'component')
        cls.original = build(SOURCE, directory / 'original')
        cls.patched = build(prepared, directory / 'patched')

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_original_exhausts_single_buffer_budget(self):
        self.assertEqual(subprocess.run([str(self.original), 'budget'], timeout=5).returncode, 1)

    def test_binary_bytes_fit_single_buffer_budget(self):
        self.assertEqual(subprocess.run([str(self.patched), 'budget'], timeout=5).returncode, 0)

    def test_file_errors_and_short_reads_are_rejected(self):
        self.assertEqual(subprocess.run([str(self.patched), 'edges'], timeout=5).returncode, 0)


if __name__ == '__main__':
    unittest.main()
