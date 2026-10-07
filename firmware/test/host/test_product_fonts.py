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
struct lv_font_t { int32_t size; const lv_font_t *fallback = nullptr; };
inline constexpr lv_font_t lv_font_montserrat_10{10}, lv_font_montserrat_12{12},
    lv_font_montserrat_14{14}, lv_font_montserrat_16{16}, lv_font_montserrat_18{18},
    lv_font_montserrat_20{20}, lv_font_montserrat_32{32};
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
    std::map<std::string, RuntimeFontResource> resources;
};
}
'''
HARNESS = r'''
#include <cassert>
#include <memory>
#include <new>
#include <set>
#include <vector>
#include <boost/unordered/unordered_flat_set.hpp>
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

namespace esp_brookesia::gui {
struct TreeRecord { Environment environment; };
struct Runtime {
    struct Impl {
        std::map<std::string, RuntimeFontResource> global_fonts;
        std::map<std::string, std::string> default_fonts_by_language;
        StyleSet compose_style_set(const TreeRecord &, const Node &node) const { return {node.style, {}, {}}; }
        void resolve_style_set_color_fields(const TreeRecord &, StyleSet &) const {}
        bool is_builtin_default_font_id(std::string_view id) const { return id == "default"; }
        ResolvedStyle resolve_style(const TreeRecord &, const Node &) const;
    };
};
#define BROOKESIA_LOGD(...) ((void)0)
#define BROOKESIA_LOGW(...) ((void)0)
__RESOLVE_STYLE__
}

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
    assert(kerning == LV_FONT_KERNING_NONE && cache_size >= 16 && cache_size <= 96);
    assert(cache_size * static_cast<size_t>(size) * size <= 96 * 24 * 24 || size > 24);
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
    for (const auto &[id, registered] : resources) {
        for (const auto &variant : registered.native_fonts) {
            auto *font = reinterpret_cast<lv_font_t *>(variant.native_src);
            assert(live_fonts.contains(font) || (font->fallback && live_fonts.contains(const_cast<lv_font_t *>(font->fallback))));
        }
    }
    ++backend_destructions;
}
bool Backend::register_font_resource(const esp_brookesia::gui::RuntimeFontResource &input) {
    ++registrations;
    resources.insert_or_assign(input.id, input);
    if (input.id == "zh_CN") resource = input;
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
void check_mixed_language_default(const Backend &backend) {
    using namespace esp_brookesia::gui;
    Runtime::Impl runtime;
    runtime.global_fonts = backend.resources;
    for (const auto &language : {"en", "zh_CN"}) {
        TreeRecord tree;
        tree.environment.language = language;
        for (const bool explicit_default : {false, true}) {
            Node node;
            if (explicit_default) node.style.font = "default";
            const auto resolved = runtime.resolve_style(tree, node);
            assert(!resolved.resolved_font.native_fonts.empty());
            assert(resolved.resolved_font.font_id == "default");
            for (const auto &variant : resolved.resolved_font.native_fonts) {
                auto *font = reinterpret_cast<const lv_font_t *>(variant.native_src);
                assert(font->fallback && live_fonts.contains(const_cast<lv_font_t *>(font->fallback)));
                assert(font->fallback->size == variant.native_size);
                const std::vector<int32_t> latin_sizes{10, 12, 14, 16, 18, 20, 32};
                int32_t expected_latin_size = 10;
                for (auto size : latin_sizes) if (size <= variant.native_size) expected_latin_size = size;
                assert(font->size == expected_latin_size);
                assert(font->fallback->fallback == nullptr);
            }
        }
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
        check_resource(*backend);
        check_mixed_language_default(*backend);
        assert(registrations == 2);
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
            runtime_source = (COMPONENTS / 'espressif__brookesia_gui_interface/src/runtime_style.cpp').read_text()
            start = runtime_source.index('ResolvedStyle Runtime::Impl::resolve_style(')
            end = runtime_source.index('std::shared_ptr<const ResolvedStyle>', start)
            harness.write_text(HARNESS.replace('__RESOLVE_STYLE__', runtime_source[start:end]))
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
            subprocess.run([str(binary)], check=True, text=True, timeout=15)


if __name__ == '__main__':
    unittest.main()
