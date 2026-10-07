"""Execute Core document loading with product, original, retry and preview paths."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class AppDocumentPresentationTest(unittest.TestCase):
    def test_product_document_keeps_original_resource_base_and_loading_owner(self):
        with tempfile.TemporaryDirectory(prefix='app-document-presentation-') as directory:
            temporary = Path(directory)
            component = prepare(ROOT / 'firmware/managed_components/espressif__brookesia_system_core',
                                ROOT / 'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json',
                                temporary / 'core')
            source = (component / 'src/system/gui.cpp').read_text()
            start = source.index('std::expected<void, std::string> System::Impl::ensure_gui_loaded(')
            method = source[start:source.index('std::expected<void, std::string> System::Impl::prepare_installed_app_gui(', start)]
            code = r'''
#include <cassert>
#include <expected>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS(...)
#define BROOKESIA_LOGD(...)
#define BROOKESIA_LOGW(...)
namespace gui {using DocumentId=int;}
struct Environment {int width=466;};
struct Manifest {std::string id="original-app",resource="original/res";};
enum class GuiRootKind {None,File,JsonString};
struct GuiDescriptor {GuiRootKind root_kind=GuiRootKind::File;std::string root="root.json";};
struct Runtime {
    bool fail=false;int file_loads=0,json_loads=0;std::string json,base;Environment environment;
    std::expected<int,std::string> load_file(std::string path,Environment env){++file_loads;base=path;environment=env;return fail?std::unexpected("load failed"):std::expected<int,std::string>{1};}
    std::expected<int,std::string> load_json(std::string id,std::string_view text,std::string dir,Environment env){
        assert(id=="original-app");++json_loads;json=text;base=dir;environment=env;
        return fail?std::unexpected("load failed"):std::expected<int,std::string>{1};
    }
    bool unload(int){return true;}
};
struct System {
    struct Config {
        struct AppPresentation {Environment environment;std::optional<int>viewport;std::string_view root_document;};
        std::function<AppPresentation(const Manifest&,const Environment&)> app_presentation;
        bool enable_gui_live_preview=true;int gui_live_preview_options=0;
    };
    struct AppRecord {
        struct Info {Manifest manifest;}info;
        GuiDescriptor gui_descriptor;std::optional<int>document_id;
        std::optional<Config::AppPresentation>presentation;
    };
    struct Impl {
        Config config_;Environment environment_;Runtime runtime;
        Runtime *gui_runtime_=&runtime;int previews=0;
        std::string resolve_app_resource_dir(const Manifest&manifest){return manifest.resource;}
        std::string resolve_app_resource_path(const Manifest&manifest,std::string root){return manifest.resource+"/"+root;}
        std::expected<void,std::string> enable_live_preview_for_document(int,int){++previews;return {};}
        std::expected<void,std::string> ensure_gui_loaded(AppRecord&);
    };
};
''' + method + r'''
int main(){
    System::Impl owner;System::AppRecord original;
    assert(owner.ensure_gui_loaded(original));
    assert(owner.runtime.file_loads==1 && owner.previews==1 && owner.runtime.base=="original/res/root.json");
    owner.config_.app_presentation=[](const Manifest&,const Environment&){return System::Config::AppPresentation{{466},{},"product-round-document"};};
    System::AppRecord adapted;
    assert(owner.ensure_gui_loaded(adapted));
    assert(owner.runtime.json_loads==1 && owner.runtime.json=="product-round-document");
    assert(owner.runtime.base=="original/res" && owner.previews==1);
    assert(adapted.gui_descriptor.root=="root.json" && adapted.info.manifest.resource=="original/res");
    assert(owner.ensure_gui_loaded(adapted) && owner.runtime.json_loads==1);
    owner.runtime.fail=true;System::AppRecord retry;
    assert(!owner.ensure_gui_loaded(retry) && !retry.document_id);
    owner.runtime.fail=false;assert(owner.ensure_gui_loaded(retry));
    owner.config_.app_presentation={};System::AppRecord native;
    native.gui_descriptor={GuiRootKind::JsonString,"native-inline"};
    assert(owner.ensure_gui_loaded(native) && owner.runtime.json=="native-inline");
    System::AppRecord absent;absent.gui_descriptor.root_kind=GuiRootKind::None;
    assert(owner.ensure_gui_loaded(absent) && !absent.document_id);
}
'''
            test = temporary / 'main.cpp'
            test.write_text(code)
            binary = temporary / 'test'
            subprocess.run(['c++', '-std=c++23', str(test), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
