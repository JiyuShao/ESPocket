"""Locked Settings resource compatibility and production adapter behavior."""

import json
from pathlib import Path
import re
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]
COMPONENT = ROOT / "firmware/components/espocket_system"
SETTINGS = ROOT / "firmware/managed_components/espressif__brookesia_app_settings"


class SettingsCompatibility(unittest.TestCase):
    def test_locked_resources_match_adapter(self):
        lock = (ROOT / "firmware/dependencies.lock").read_text()
        section = lock.split("  espressif/brookesia_app_settings:\n", 1)[1].split("\n  espressif/", 1)[0]
        self.assertRegex(section, r"(?m)^    version: 0\.8\.3$")
        self.assertIn("component_hash: 46dd5de734a74672203240420fd52967b3f61f9882b600813d24b1fccd3204a5", section)
        self.assertRegex((ROOT / "firmware/main/idf_component.yml").read_text(),
                         r'brookesia_app_settings: "0\.8\.3"')
        flow = json.loads((SETTINGS / "package/res/flows/content.json").read_text())
        source = (COMPONENT / "src/settings_navigation_adapter.cpp").read_text()
        mappings = dict(re.findall(r'\{"([a-z_]+)", "(settings\.[a-z_]+)"\}', source))
        self.assertEqual(set(mappings), set(flow["screens"]))
        self.assertEqual(flow["id"], "settings_content")
        self.assertEqual(mappings[flow["initial"]], "settings.root")
        self.assertEqual(len(set(mappings.values())), len(mappings))
        header = json.loads((SETTINGS / "package/res/screens/header.json").read_text())
        self.assertIn("settings.header.back", json.dumps(header))
        # Every declared child has an official route back; this is a prerequisite,
        # not proof that upstream business side effects are correct on hardware.
        routes = {(t["action"], t["to"]) for t in flow["transitions"]}
        required = {
            ("settings.open.home", "settings_home"),
            ("settings.back.device", "settings_home"),
            ("settings.back.wifi", "settings_home"),
            ("settings.back.wifi_connect", "wifi"),
            ("settings.back.sound", "settings_home"),
            ("settings.back.display", "settings_home"),
            ("settings.back.language", "more"),
            ("settings.back.time_zone", "more"),
            ("settings.back.debug", "my_device"),
        }
        self.assertTrue(required <= routes)

    def test_production_adapter_delegates_and_reads_live_page(self):
        with tempfile.TemporaryDirectory(prefix="espocket-settings-test-") as directory:
            temp = Path(directory)
            (temp / "brookesia").mkdir()
            (temp / "brookesia/system_core.hpp").write_text(STUB)
            (temp / "esp_log.h").write_text('#pragma once\n#define ESP_LOGW(...) ((void)0)\n')
            (temp / "test.cpp").write_text(TEST)
            binary = temp / "test"
            subprocess.run([
                os.environ.get("CXX", "clang++"), "-std=c++23", "-pthread", "-I", str(temp),
                "-I", str(COMPONENT / "include"), "-I",
                str(ROOT / "firmware/components/espocket_navigation/include"),
                str(COMPONENT / "src/settings_navigation_adapter.cpp"),
                str(temp / "test.cpp"), "-o", str(binary),
            ], check=True, capture_output=True, text=True)
            subprocess.run([str(binary)], check=True)


STUB = r'''
#pragma once
#include <expected>
#include <optional>
#include <string>
#include <string_view>
#include <cstdint>
namespace esp_brookesia::system::core {
using TimerId = uint32_t;
struct AppManifest { std::string id; };
struct AppGuiDescriptor { int marker = 0; };
struct AppGuiRuntime {
    std::optional<std::string> screen = "settings_home";
    std::optional<std::string> get_screen_flow_state(std::string_view flow) {
        return flow == "settings_content" ? screen : std::nullopt;
    }
};
struct AppContext {
    AppGuiRuntime runtime;
    AppGuiRuntime &gui() { return runtime; }
};
class IApp {
public:
    virtual ~IApp() = default;
    virtual AppManifest get_manifest() const = 0;
    virtual AppGuiDescriptor get_gui_descriptor() const { return {}; }
    virtual std::expected<void, std::string> on_install(AppContext &) { return {}; }
    virtual void on_uninstall(AppContext &) {}
    virtual std::expected<void, std::string> on_start(AppContext &) { return {}; }
    virtual std::expected<void, std::string> on_pause(AppContext &) { return {}; }
    virtual std::expected<void, std::string> on_resume(AppContext &) { return {}; }
    virtual std::expected<void, std::string> on_stop(AppContext &) { return {}; }
    virtual std::expected<void, std::string> on_action(AppContext &, std::string_view) { return {}; }
    virtual std::expected<void, std::string> on_timer(AppContext &, TimerId, std::string_view) { return {}; }
};
}
'''

TEST = r'''
#include <cassert>
#include "espocket/settings_navigation_adapter.hpp"
using namespace esp_brookesia::system::core;
struct FakeSettings : IApp {
    int installed = 0, uninstalled = 0, started = 0, stopped = 0;
    int paused = 0, resumed = 0, backs = 0, actions = 0, timers = 0;
    AppManifest get_manifest() const override { return {"brookesia.general.settings"}; }
    AppGuiDescriptor get_gui_descriptor() const override { return {42}; }
    std::expected<void, std::string> on_install(AppContext &) override { ++installed; return {}; }
    void on_uninstall(AppContext &) override { ++uninstalled; }
    std::expected<void, std::string> on_start(AppContext &c) override {
        ++started; c.runtime.screen = "settings_home"; return {};
    }
    std::expected<void, std::string> on_pause(AppContext &) override { ++paused; return {}; }
    std::expected<void, std::string> on_resume(AppContext &) override { ++resumed; return {}; }
    std::expected<void, std::string> on_stop(AppContext &) override { ++stopped; return {}; }
    std::expected<void, std::string> on_action(AppContext &c, std::string_view a) override {
        ++actions;
        if (a == "settings.header.back") {
            ++backs;
            c.runtime.screen = *c.runtime.screen == "wifi_connect" ? "wifi" : "settings_home";
        } else if (a == "open_wifi") { c.runtime.screen = "wifi"; }
        else if (a == "fail") { return std::unexpected("upstream_error"); }
        return {};
    }
    std::expected<void, std::string> on_timer(AppContext &, TimerId id, std::string_view name) override {
        assert(id == 7 && name == "upstream_timer"); ++timers; return {};
    }
};
int main() {
    auto app = std::make_shared<FakeSettings>();
    espocket::SettingsNavigationAdapter adapter(app);
    AppContext context;
    assert(adapter.get_manifest().id == app->get_manifest().id);
    assert(adapter.get_gui_descriptor().marker == 42);
    assert(!adapter.snapshot() && !adapter.edge_back_enabled());
    assert(adapter.on_install(context) && app->installed == 1);
    assert(adapter.on_start(context));
    assert(adapter.snapshot()->page_id == "settings.root");
    assert(!adapter.request_back() && app->backs == 0);
    assert(adapter.on_action(context, "open_wifi"));
    assert(adapter.snapshot()->can_back && adapter.edge_back_enabled());
    context.runtime.screen = "wifi_connect";
    assert(adapter.snapshot()->page_id == "settings.wifi_connect");
    assert(adapter.request_back() && adapter.snapshot()->page_id == "settings.wifi");
    assert(adapter.on_action(context, "settings.header.back"));
    assert(adapter.snapshot()->page_id == "settings.root" && !adapter.edge_back_enabled());
    assert(app->backs == 2);
    context.runtime.screen = "unknown_new_screen";
    assert(!adapter.snapshot() && !adapter.request_back() && app->backs == 2);
    assert(!adapter.edge_back_enabled());
    context.runtime.screen.reset();
    assert(!adapter.snapshot() && !adapter.request_back());
    context.runtime.screen = "display";
    assert(adapter.on_timer(context, 7, "upstream_timer") && app->timers == 1);
    assert(adapter.edge_back_enabled());
    assert(adapter.on_pause(context) && app->paused == 1);
    assert(!adapter.snapshot() && !adapter.edge_back_enabled());
    assert(adapter.on_resume(context) && app->resumed == 1);
    assert(adapter.snapshot()->page_id == "settings.display");
    auto failure = adapter.on_action(context, "fail");
    assert(!failure && failure.error() == "upstream_error");
    assert(adapter.on_stop(context) && app->stopped == 1);
    assert(!adapter.snapshot() && !adapter.request_back());
    assert(adapter.on_start(context) && adapter.snapshot()->page_id == "settings.root");
    adapter.on_uninstall(context);
    assert(app->uninstalled == 1 && !adapter.snapshot());
}
'''

if __name__ == "__main__":
    unittest.main()
