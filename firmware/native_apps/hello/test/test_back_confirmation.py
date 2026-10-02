"""Exercise the production Hello App against the real Navigator and a fake GUI/Timer port."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

APP = Path(__file__).resolve().parents[1]
NAVIGATION = APP.parents[1] / 'components/espocket_navigation'

STUB = r'''
#pragma once
#include <cstdint>
#include <expected>
#include <map>
#include <string>
#include <string_view>
#include <vector>
namespace esp_brookesia::system::core {
using TimerId = uint32_t;
enum class AppKind { Native };
enum class GuiRootKind { JsonString };
enum class GuiAppLayer { AppDefault };
struct AppManifest {
    std::string id, name;
    std::map<std::string, std::string> localized_names;
    std::string version;
    AppKind kind;
    bool visible;
};
struct Flow { std::string screen_flow; GuiAppLayer layer; };
struct AppGuiDescriptor {
    GuiRootKind root_kind;
    std::string root;
    std::vector<std::string> resources;
    std::vector<Flow> screen_flows;
};
struct Gui {
    std::map<std::string, std::string> texts;
    bool fail = false;
    std::expected<void, std::string> subscribe_action(std::string_view) { return {}; }
    std::expected<void, std::string> set_text(std::string_view path, std::string_view text) {
        if (fail) return std::unexpected("gui_failed");
        texts[std::string(path)] = text; return {};
    }
    std::expected<void, std::string> trigger_screen_flow(std::string_view, std::string_view) {
        if (fail) return std::unexpected("presentation_failed");
        return {};
    }
};
struct Timer {
    bool fail = false, stopped = false;
    std::expected<TimerId, std::string> start_periodic(std::string_view, int) {
        if (fail) return std::unexpected("timer_failed");
        return 42;
    }
    bool stop(TimerId) { stopped = true; return true; }
};
struct AppContext {
    Gui gui_port; Timer timer_port;
    Gui &gui() { return gui_port; }
    Timer &timer() { return timer_port; }
};
struct IApp {
    virtual ~IApp() = default;
    virtual AppManifest get_manifest() const = 0;
    virtual AppGuiDescriptor get_gui_descriptor() const = 0;
    virtual std::expected<void, std::string> on_start(AppContext &) = 0;
    virtual std::expected<void, std::string> on_stop(AppContext &) = 0;
    virtual std::expected<void, std::string> on_action(AppContext &, std::string_view) = 0;
    virtual std::expected<void, std::string> on_timer(AppContext &, TimerId, std::string_view) = 0;
};
}
'''

TEST = r'''
#include "espocket/hello_app.hpp"
#include "espocket/page_navigator.hpp"
#include <cassert>
extern const char gui_json[] asm("_binary_hello_gui_json_start");
const char gui_json[] = "{}";
using namespace espocket;
using namespace esp_brookesia::system::core;
int main() {
    HelloApp app;
    AppContext context;
    auto result = PageNavigator::create(app.get_page_declaration(),
        [&](auto from, auto to) { return app.present_page(from, to); });
    assert(result);
    auto navigator = std::make_shared<PageNavigator>(std::move(*result));
    app.set_navigator(navigator);
    context.timer_port.fail = true;
    assert(!app.on_start(context));
    context.timer_port.fail = false;
    assert(app.on_start(context));
    assert(navigator->start() && !navigator->snapshot().can_back);
    assert(app.on_action(context, "hello.open_detail"));
    assert(navigator->request_back(0)); // Default remains immediate.
    assert(navigator->snapshot().page_id == "root");
    assert(app.on_action(context, "hello.open_detail"));
    assert(app.on_action(context, "hello.toggle_confirm"));
    auto pending = navigator->request_back(10);
    assert(pending && pending->has_value());
    assert(navigator->snapshot().back_pending && !navigator->snapshot().can_back);
    assert(navigator->request_back(11).error() == NavigationError::BackPending);
    assert(!app.on_action(context, "hello.toggle_confirm"));
    assert(app.on_timer(context, 42, "hello.back_status"));
    assert(context.gui_port.texts["/detail/hint"] == "Back? Allow or Cancel");
    assert(app.on_action(context, "hello.cancel_back"));
    assert(navigator->snapshot().page_id == "detail" && navigator->snapshot().can_back);
    assert(!app.on_action(context, "hello.allow_back"));
    assert(navigator->request_back(20));
    assert(app.on_action(context, "hello.allow_back"));
    assert(navigator->snapshot().page_id == "root" && !navigator->snapshot().can_back);
    assert(app.on_action(context, "hello.open_detail"));
    assert(navigator->request_back(100));
    assert(navigator->expire_back(15100) == NavigationError::BackTimeout);
    assert(app.on_timer(context, 42, "hello.back_status"));
    assert(context.gui_port.texts["/detail/hint"] == "Back expired or invalidated");
    assert(!app.on_action(context, "hello.allow_back"));
    assert(navigator->request_back(16000));
    context.gui_port.fail = true;
    assert(!app.on_action(context, "hello.allow_back"));
    assert(navigator->snapshot().page_id == "detail" && navigator->snapshot().can_back);
    context.gui_port.fail = false;
    auto old = navigator->request_back(17000);
    assert(old && old->has_value());
    assert(app.on_stop(context)); // PWR/lifecycle cleanup cannot be deferred by the App.
    navigator->stop();
    assert(context.timer_port.stopped);
    assert(navigator->complete_back(old->value(), true).error() == NavigationError::StaleRequest);
    assert(app.on_start(context) && navigator->start());
    assert(!app.on_action(context, "hello.allow_back"));
    assert(app.on_action(context, "hello.open_detail"));
    assert(navigator->request_back(20000)); // New instance resets confirm to Off.
    assert(navigator->snapshot().page_id == "root");
    assert(app.on_stop(context));
    navigator->stop();
}
'''


class BackConfirmationTest(unittest.TestCase):
    def test_native_app_confirmation_and_cleanup(self):
        with tempfile.TemporaryDirectory(prefix='espocket-hello-back-') as directory:
            temp = Path(directory)
            (temp / 'brookesia').mkdir()
            (temp / 'brookesia/system_core.hpp').write_text(STUB)
            (temp / 'esp_log.h').write_text('#pragma once\n#define ESP_LOGW(...)\n#define ESP_LOGI(...)\n')
            (temp / 'test.cpp').write_text(TEST)
            binary = temp / 'test'
            subprocess.run([
                os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread',
                '-I', str(temp), '-I', str(APP / 'include'), '-I', str(NAVIGATION / 'include'),
                str(APP / 'src/hello_app.cpp'), str(NAVIGATION / 'src/page_navigator.cpp'),
                str(temp / 'test.cpp'), '-o', str(binary),
            ], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
