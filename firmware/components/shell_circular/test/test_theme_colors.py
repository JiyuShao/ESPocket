"""Execute native palette loading against the actual product theme resources."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]
COMPONENT = ROOT / 'firmware/components/shell_circular'


class ThemeColorsTest(unittest.TestCase):
    def test_product_palette_and_invalid_resources(self):
        source = (COMPONENT / 'src/shell_document.cpp').read_text()
        methods = source[source.index('std::expected<void, std::string> CircularShell::load_theme_colors()'):
                         source.index('esp_brookesia::system::core::AppGuiDescriptor')]
        harness = r'''
#include <boost/json.hpp>
#include <boost/json/src.hpp>
#include <cassert>
#include <charconv>
#include <expected>
#include <fstream>
#include <functional>
#include <map>
#include <string>
#include <string_view>
namespace espocket {
struct Gui {std::string theme;std::string get_theme() const {return theme;}};
struct Context {Gui value;Gui& gui(){return value;}};
struct CircularShell {
    Context* context_;
    struct {std::function<std::expected<std::string_view,std::string>(std::string_view)> theme_resource;} host_;
    std::map<std::string,uint32_t,std::less<>> theme_colors_;
    std::expected<void,std::string> load_theme_colors();
    uint32_t theme_color(std::string_view token) const;
};
''' + methods + r'''
}
int main(int argc,char** argv) {
    using namespace espocket;
    assert(argc==3);
    Context context;CircularShell shell{.context_=&context};
    assert(!shell.load_theme_colors());
    std::string resource;
    shell.host_.theme_resource=[&](std::string_view theme)->std::expected<std::string_view,std::string>{
        assert(theme==context.value.theme);return resource;
    };
    for(int i=1;i<3;++i) {
        context.value.theme=i==1?"light":"dark";
        std::ifstream input(argv[i]);resource.assign(std::istreambuf_iterator<char>(input),{});
        assert(shell.load_theme_colors());
        auto colors=boost::json::parse(resource).at("assets").at(0).at("data").at("colors");
        for(const auto& [token,color]:shell.theme_colors_) {
            auto dot=token.find('.');
            auto text=colors.at(token.substr(0,dot)).at(token.substr(dot+1)).as_string();
            assert(color==std::stoul(std::string(text.data()+1,text.size()-1),nullptr,16));
        }
        assert(shell.theme_color("primary.fill")!=shell.theme_color("primary.on"));
    }
    auto saved=shell.theme_colors_;
    for(auto broken:{"not json","{}","{\"assets\":[{\"data\":{\"colors\":{\"bg\":{\"base\":\"#zzzzzz\"}}}}]}"}) {
        resource=broken;assert(!shell.load_theme_colors());assert(saved==shell.theme_colors_);
    }
}
'''
        with tempfile.TemporaryDirectory(prefix='espocket-theme-colors-') as temporary:
            cpp = Path(temporary) / 'test.cpp'
            binary = Path(temporary) / 'test'
            cpp.write_text(harness)
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-DBOOST_NO_USER_CONFIG',
                            '-I', str(ROOT / 'firmware/managed_components/espressif__esp-boost/src'),
                            str(cpp), '-o', str(binary)], check=True)
            subprocess.run([str(binary), *[str(ROOT / f'firmware/components/espocket_system/resources/{mode}_theme.json')
                                           for mode in ('light', 'dark')]], check=True)
