"""Run the production Native installation boundary with a fake Core."""

from pathlib import Path
import os
import subprocess
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1]
NAVIGATION = COMPONENT.parent / 'espocket_navigation'

STUB = r'''
#pragma once
#include <cstdint>
#include <expected>
#include <memory>
#include <string>
namespace esp_brookesia::system::core {
using AppId = uint32_t;
struct AppManifest { std::string id; };
struct IApp {
    virtual ~IApp() = default;
    virtual AppManifest get_manifest() const = 0;
};
struct System {
    int installations = 0;
    bool fail = false;
    std::expected<AppId, std::string> install_app(std::shared_ptr<IApp>) {
        ++installations;
        if (fail) { return std::unexpected("core_install_failed"); }
        return 42;
    }
};
}
'''

TEST = r'''
#include <cassert>
#include "espocket/native_page_installation.hpp"
using namespace espocket;
using namespace esp_brookesia::system::core;
struct Native : IApp {
    AppManifest get_manifest() const override { return {"app.native"}; }
};
int main() {
    System core;
    auto app = std::make_shared<Native>();
    PageDeclaration declaration{
        .app_id = "app.native", .root_page_id = "root", .page_ids = {"root", "detail"}
    };
    auto presenter = [](std::string_view, std::string_view) { return true; };
    assert(!install_native_page_app(core, nullptr, declaration, presenter));
    auto mismatched = declaration;
    mismatched.app_id = "other";
    assert(!install_native_page_app(core, app, mismatched, presenter));
    auto invalid = declaration;
    invalid.page_ids = {"detail"};
    assert(!install_native_page_app(core, app, invalid, presenter));
    invalid = declaration;
    invalid.cards = {{"card", "missing"}};
    assert(!install_native_page_app(core, app, invalid, presenter));
    assert(core.installations == 0);
    core.fail = true;
    auto failed = install_native_page_app(core, app, declaration, presenter);
    assert(!failed && failed.error() == "core_install_failed" && core.installations == 1);
    core.fail = false;
    auto installed = install_native_page_app(core, app, declaration, presenter);
    assert(installed && installed->app_id == 42 && core.installations == 2);
    assert(installed->navigator->snapshot().app_id == "app.native");
    assert(installed->navigator->snapshot().page_id.empty());
    assert(installed->navigator->start() && installed->navigator->push("detail"));
    installed->navigator->set_back_handler([](const auto &, uint64_t) { return BackDecision::Defer; });
    auto back = installed->navigator->request_back(0);
    assert(back && back->has_value());
    installed->navigator->stop();
    assert(installed->navigator->snapshot().page_id.empty());
    assert(!installed->navigator->complete_back(back->value(), true));
}
'''


class NativeInstallationTest(unittest.TestCase):
    def test_declarations_gate_the_real_installation_boundary(self):
        with tempfile.TemporaryDirectory(prefix='espocket-native-install-test-') as directory:
            temp = Path(directory)
            (temp / 'brookesia').mkdir()
            (temp / 'brookesia/system_core.hpp').write_text(STUB)
            (temp / 'test.cpp').write_text(TEST)
            binary = temp / 'test'
            subprocess.run([
                os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread',
                '-I', str(temp), '-I', str(COMPONENT / 'include'),
                '-I', str(NAVIGATION / 'include'),
                str(COMPONENT / 'src/native_page_installation.cpp'),
                str(NAVIGATION / 'src/page_navigator.cpp'), str(temp / 'test.cpp'),
                '-o', str(binary),
            ], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
