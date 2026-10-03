"""Execute actual Core SystemGuiAccess embedded-theme marshalling and failures."""
import os
from pathlib import Path
import sys
import tempfile
import subprocess
import unittest
ROOT = Path(__file__).resolve().parents[3]


class CoreThemeLoadingTest(unittest.TestCase):
    def test_thread_boundary_copies_input_and_preserves_errors(self):
        sys.path.insert(0, str(ROOT / 'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='espocket-core-theme-') as directory:
            patched = prepare(ROOT / 'firmware/managed_components/espressif__brookesia_system_core',
                              ROOT / 'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json',
                              Path(directory) / 'patched')
            text = (patched / 'src/system/gui_access.cpp').read_text()
            method = text[text.index('std::expected<void, std::string> SystemGuiAccess::load_theme_json('):text.index('std::expected<void, std::string> SystemGuiAccess::load_theme_file(')]
            harness = r'''
#include <cassert>
#include <expected>
#include <functional>
#include <string>
#include <string_view>
constexpr int SYSTEM_GUI_TASK_GROUP=5;
struct Runtime { std::string json, directory; bool fail=false;
    std::expected<void,std::string> load_theme_json(std::string_view j,std::string_view d) {
        json=j;directory=d; if(fail) return std::unexpected("invalid theme"); return {}; }
};
struct Impl { Runtime* gui_runtime_=nullptr; bool post=true; unsigned calls=0; std::function<void()> before;
    template<class Result,class Callback> Result run_task_sync(int group,Callback cb,Result fallback) {
        assert(group==5); ++calls; if(!post) return fallback; if(before) before(); return cb(); }
};
struct System {Impl* impl_;};
struct SystemGuiAccess {System* system_=nullptr;
    std::expected<void,std::string> make_unavailable_error() const {return std::unexpected("unavailable");}
    std::expected<void,std::string> load_theme_json(std::string_view,std::string_view) const;
};
''' + method + r'''
int main() {
    SystemGuiAccess access; assert(!access.load_theme_json("x","dir"));
    Impl impl;System system{&impl};access.system_=&system;assert(!access.load_theme_json("x","dir"));
    Runtime runtime;impl.gui_runtime_=&runtime;std::string json="valid", directory="resource";
    impl.before=[&]{json="changed";directory="changed";};
    assert(access.load_theme_json(json,directory));assert(runtime.json=="valid" && runtime.directory=="resource");
    impl.before={};runtime.fail=true;auto failure=access.load_theme_json("bad","");
    assert(!failure && failure.error()=="invalid theme");
    impl.post=false;auto rejected=access.load_theme_json("x","");
    assert(!rejected && rejected.error()=="Failed to post system GUI theme load task");
}
'''
            source = Path(directory) / 'test.cpp';source.write_text(harness)
            binary = Path(directory) / 'test'
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23',str(source),'-o',str(binary)],check=True)
            subprocess.run([str(binary)],check=True,timeout=10)
