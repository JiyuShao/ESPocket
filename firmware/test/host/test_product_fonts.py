"""Compile the product font owner and exercise borrowing, locking and rollback."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
COMPONENTS = ROOT / 'firmware/managed_components'
OWNER = ROOT / 'firmware/components/espocket_system/src'

LVGL = r'''
#pragma once
#include <cstddef>
#include <cstdint>
struct lv_font_t { int32_t size; };
enum lv_font_kerning_t { LV_FONT_KERNING_NONE, LV_FONT_KERNING_NORMAL };
lv_font_t *lv_tiny_ttf_create_data_ex(const void *, size_t, int32_t, lv_font_kerning_t, size_t);
void lv_tiny_ttf_destroy(lv_font_t *);
'''
ADAPTER = r'''
#pragma once
using esp_err_t = int;
inline constexpr esp_err_t ESP_OK = 0;
esp_err_t esp_lv_adapter_lock(int32_t);
void esp_lv_adapter_unlock();
'''
BACKEND = r'''
#pragma once
#include "brookesia/gui_interface/document.hpp"
namespace esp_brookesia::gui::lvgl {
class Backend final {
public:
    ~Backend();
    bool register_font_resource(const RuntimeFontResource &);
    RuntimeFontResource resource;
};
}
'''
HARNESS = r'''
#include <cassert>
#include <memory>
#include <new>
#include <set>
#include <vector>
#include "product_fonts.hpp"
#include "esp_lv_adapter.h"
#include "brookesia/gui_lvgl/backend.hpp"

using espocket::ProductFonts;
using esp_brookesia::gui::lvgl::Backend;
const std::vector<int32_t> expected_sizes{10, 11, 12, 13, 14, 15, 16, 18, 20, 22, 24, 28, 32, 40, 48, 64};
std::set<lv_font_t *> live_fonts;
std::vector<int32_t> created_sizes;
size_t failed_creation = 0;
int lock_depth = 0;
bool adapter_available = true;
bool fail_registration = false;
bool throw_registration = false;
unsigned registrations = 0;
unsigned backend_destructions = 0;
const void *shared_data = nullptr;
size_t shared_size = 0;

esp_err_t esp_lv_adapter_lock(int32_t timeout) {
    assert(timeout == -1);
    if (!adapter_available) return 1;
    ++lock_depth;
    return ESP_OK;
}
void esp_lv_adapter_unlock() {
    assert(lock_depth > 0);
    --lock_depth;
}
lv_font_t *lv_tiny_ttf_create_data_ex(const void *data, size_t data_size,
    int32_t size, lv_font_kerning_t kerning, size_t cache_size) {
    assert(lock_depth > 0 && data != nullptr && data_size == 4);
    assert(kerning == LV_FONT_KERNING_NONE && cache_size == 4);
    if (!shared_data) { shared_data = data; shared_size = data_size; }
    assert(shared_data == data && shared_size == data_size);
    created_sizes.push_back(size);
    if (failed_creation == created_sizes.size()) return nullptr;
    auto *font = new lv_font_t{size};
    assert(live_fonts.insert(font).second);
    return font;
}
void lv_tiny_ttf_destroy(lv_font_t *font) {
    assert(lock_depth > 0 && live_fonts.erase(font) == 1);
    delete font;
}
Backend::~Backend() {
    for (const auto &variant : resource.native_fonts) {
        assert(live_fonts.contains(reinterpret_cast<lv_font_t *>(variant.native_src)));
    }
    ++backend_destructions;
}
bool Backend::register_font_resource(const esp_brookesia::gui::RuntimeFontResource &input) {
    ++registrations;
    resource = input;
    if (throw_registration) throw std::bad_alloc();
    return !fail_registration;
}
void reset_probe() {
    assert(live_fonts.empty() && lock_depth == 0);
    created_sizes.clear();
    failed_creation = 0;
    fail_registration = false;
    throw_registration = false;
    registrations = 0;
}
void check_resource(const Backend &backend) {
    const auto &resource = backend.resource;
    assert(resource.id == "zh_CN" && resource.kind == "file" && resource.primary_src == "zh_CN");
    assert(resource.languages == std::vector<std::string>{"zh_CN"});
    assert(resource.fallback_ids.empty() && resource.native_fonts.size() == expected_sizes.size());
    std::set<uintptr_t> addresses;
    for (size_t index = 0; index < expected_sizes.size(); ++index) {
        const auto &variant = resource.native_fonts[index];
        auto *font = reinterpret_cast<lv_font_t *>(variant.native_src);
        assert(variant.native_size == expected_sizes[index] && live_fonts.contains(font));
        assert(font->size == expected_sizes[index] && addresses.insert(variant.native_src).second);
    }
}
void test_success_and_repeated_prepare() {
    for (unsigned cycle = 0; cycle < 20; ++cycle) {
        reset_probe();
        auto result = ProductFonts::create();
        assert(result && created_sizes == expected_sizes && lock_depth == 0);
        auto fonts = std::move(*result);
        auto backend = std::make_unique<Backend>();
        assert(fonts->register_with(*backend));
        assert(registrations == 1);
        check_resource(*backend);
        assert(live_fonts.size() == expected_sizes.size());
        backend.reset();
        assert(live_fonts.size() == expected_sizes.size());
        fonts.reset();
        assert(live_fonts.empty() && lock_depth == 0);
    }
}
void test_creation_rollback() {
    for (size_t failure = 1; failure <= expected_sizes.size(); ++failure) {
        reset_probe();
        failed_creation = failure;
        auto result = ProductFonts::create();
        assert(!result && result.error().find(std::to_string(expected_sizes[failure - 1])) != std::string::npos);
        assert(created_sizes.size() == failure && live_fonts.empty() && lock_depth == 0);
    }
    reset_probe();
    adapter_available = false;
    auto result = ProductFonts::create();
    assert(!result && created_sizes.empty() && live_fonts.empty() && lock_depth == 0);
    adapter_available = true;
}
void test_registration_rollback() {
    for (const bool throws : {false, true}) {
        reset_probe();
        auto result = ProductFonts::create();
        assert(result);
        auto fonts = std::move(*result);
        auto backend = std::make_unique<Backend>();
        fail_registration = !throws;
        throw_registration = throws;
        bool failed = false;
        try { failed = !fonts->register_with(*backend); }
        catch (const std::bad_alloc &) { failed = true; }
        assert(failed && registrations == 1);
        check_resource(*backend);
        backend.reset();
        assert(live_fonts.size() == expected_sizes.size());
        fonts.reset();
        assert(live_fonts.empty() && lock_depth == 0);
    }
}
int main() {
    test_success_and_repeated_prepare();
    test_creation_rollback();
    test_registration_rollback();
    assert(backend_destructions == 22);
}
'''


class ProductFontsTest(unittest.TestCase):
    def test_actual_owner_locks_borrows_and_rolls_back(self):
        with tempfile.TemporaryDirectory(prefix='espocket-product-fonts-') as directory:
            temporary = Path(directory)
            shims = temporary / 'shims'
            for relative, contents in {
                'lvgl.h': LVGL,
                'esp_lv_adapter.h': ADAPTER,
                'brookesia/gui_lvgl/backend.hpp': BACKEND,
            }.items():
                target = shims / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(contents)
            harness = temporary / 'main.cpp'
            harness.write_text(HARNESS)
            embedded = temporary / 'font.S'
            embedded.write_text('.data\n.globl _binary_espocket_cjk_otf_start\n'
                                '.globl _binary_espocket_cjk_otf_end\n'
                                '_binary_espocket_cjk_otf_start:\n.byte 1,2,3,4\n'
                                '_binary_espocket_cjk_otf_end:\n')
            binary = temporary / 'probe'
            command = [os.environ.get('CXX', 'clang++'), '-std=c++23', '-O2',
                       '-Wall', '-Wextra', '-Werror', '-DBOOST_NO_USER_CONFIG']
            for include in [shims, OWNER,
                            COMPONENTS / 'espressif__brookesia_gui_interface/include',
                            COMPONENTS / 'espressif__brookesia_lib_utils/include',
                            COMPONENTS / 'espressif__esp-boost/src']:
                command.extend(['-I', str(include)])
            command.extend([str(OWNER / 'product_fonts.cpp'), str(harness),
                            str(embedded), '-o', str(binary)])
            subprocess.run(command, check=True, capture_output=True, text=True, timeout=90)
            subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=15)


if __name__ == '__main__':
    unittest.main()
