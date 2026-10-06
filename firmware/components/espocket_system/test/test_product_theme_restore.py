"""Exercise the real product startup preference restoration boundary."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 'firmware/components/espocket_system/src/system.cpp'


class ProductThemeRestoreTest(unittest.TestCase):
    def test_saved_theme_is_applied_without_overwriting_the_preference(self):
        source = SOURCE.read_text()
        self.assertTrue('System::restore_product_theme()' in source,
                      'product startup never restores the saved theme')
        start = source.index('std::expected<void, std::string> System::init_product_theme()')
        end = source.index('\nesp_brookesia::system::core::SystemInfo', start)
        method = source[start:end]
        harness = r'''
#include <cassert>
#include <expected>
#include <optional>
#include <string>
#include <string_view>
#include <vector>
#define ESP_LOGI(...) ((void)0)
#define ESP_LOGW(...) ((void)0)
constexpr const char *TAG="test";
constexpr char dark_theme_start[]="dark-json", light_theme_start[]="light-json";
constexpr auto dark_theme_end=dark_theme_start+sizeof(dark_theme_start);
constexpr auto light_theme_end=light_theme_start+sizeof(light_theme_start);
namespace espocket {
struct Gui { std::string selected; bool fail=false, light_fail=false, load_fail=false;std::vector<std::string> loaded;
    std::expected<void,std::string> load_theme_json(std::string_view json) {
        if(load_fail)return std::unexpected("parse failure");loaded.emplace_back(json);return {}; }
    std::expected<void,std::string> set_theme(std::string_view id,bool reapply) {
        assert(!reapply);selected=id;if(fail || (light_fail && id=="light"))return std::unexpected("backend failure");return {}; }
};
struct System { Gui gui;std::optional<std::string> saved;std::vector<std::string> calls;
    std::optional<std::string> get_stored_gui_theme_id() { return saved; }
    Gui& system_gui() { return gui; }
    void begin_gui_preferences_restore() { calls.push_back("begin"); }
    void mark_gui_preferences_restored() { calls.push_back("restored"); }
    std::expected<void,std::string> init_product_theme();
    std::expected<void,std::string> restore_product_theme();
};
''' + method + r'''
}
int main() {
    using espocket::System;
    System boot;boot.saved="light";assert(boot.init_product_theme());
    assert((boot.gui.loaded==std::vector<std::string>{"dark-json","light-json"}));
    assert(boot.gui.selected=="light");
    System parse_failed;parse_failed.gui.load_fail=true;assert(!parse_failed.init_product_theme());
    assert(parse_failed.gui.selected.empty() && parse_failed.calls.empty());
    System first;assert(first.restore_product_theme());assert(first.gui.selected=="dark");
    assert(!first.saved);assert((first.calls==std::vector<std::string>{"begin","restored"}));
    System light;light.saved="light";assert(light.restore_product_theme());
    assert(light.gui.selected=="light" && light.saved=="light");
    System invalid;invalid.saved="unknown";assert(invalid.restore_product_theme());
    assert(invalid.gui.selected=="dark" && invalid.saved=="unknown");
    assert((invalid.calls==std::vector<std::string>{"begin","restored"}));
    System fallback;fallback.saved="light";fallback.gui.light_fail=true;
    assert(fallback.restore_product_theme());assert(fallback.gui.selected=="dark" && fallback.saved=="light");
    fallback.gui.light_fail=false;assert(fallback.restore_product_theme());assert(fallback.gui.selected=="light");
    System default_failed;default_failed.saved="dark";default_failed.gui.fail=true;
    assert(!default_failed.restore_product_theme());assert(default_failed.saved=="dark");
    System failed;failed.saved="light";failed.gui.fail=true;
    auto failure=failed.restore_product_theme();assert(!failure);
    assert(failure.error().find("backend failure")!=std::string::npos);
    assert(failed.saved=="light" && failed.calls.size()==1);
}
'''
        # Selection occurs after registering both themes, before starting Apps.
        init = source[source.index('System::init_product_theme()'):source.index('System::restore_product_theme()')]
        self.assertLess(init.index('load_theme_json(theme)'), init.index('restore_product_theme();'))
        on_init = source[source.index('System::on_init()'):]
        self.assertLess(on_init.index('init_product_theme();'), on_init.index('install_app('))
        with tempfile.TemporaryDirectory(prefix='espocket-theme-restore-') as directory:
            cpp = Path(directory) / 'test.cpp'
            binary = Path(directory) / 'test'
            cpp.write_text(harness)
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(cpp), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=10)
