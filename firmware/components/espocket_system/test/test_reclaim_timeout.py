"""Execute the production timeout boundary with independent model configurations."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1]
STUB = r'''
#pragma once
#include <atomic>
#include <cstdint>
#include <expected>
#include <optional>
#include <string>
namespace esp_brookesia::system::core {
using AppId = uint32_t;
constexpr AppId INVALID_APP_ID = 0;
enum class AppKind { Native, Runtime };
struct Manifest { AppKind kind; bool visible = true; std::string id = "sample"; };
struct AppInfo { Manifest manifest; };
}
namespace espocket {
struct System {
    std::atomic_bool stopping_ = false, display_on_ = true;
    uint32_t resume_app_id_ = 7;
    bool display_ok = true, stop_ok = true;
    int stops = 0, display_calls = 0;
    std::optional<esp_brookesia::system::core::AppInfo> app;
    bool foreground = false;
    auto get_active_app() const { return foreground ? app : std::nullopt; }
    std::expected<void, std::string> set_display_on(bool value) {
        ++display_calls;
        if (!display_ok) return std::unexpected("display_failed");
        display_on_ = value; return {};
    }
    auto get_app(uint32_t) const { return app; }
    std::expected<void, std::string> stop_app(uint32_t id) {
        if (id != resume_app_id_) return std::unexpected("wrong_target");
        ++stops;
        return stop_ok ? std::expected<void, std::string>{} : std::unexpected("stop_failed");
    }
    void handle_screen_timeout();
};
}
'''
TEST = r'''
#include "espocket/system.hpp"
#include <cassert>
using namespace espocket;
using namespace esp_brookesia::system::core;
int main() {
    System conversation;
    conversation.app = AppInfo{{AppKind::Runtime, true, "brookesia.general.ai_chatbot"}};
    conversation.foreground = true;
    conversation.handle_screen_timeout();
    assert(conversation.display_on_ && conversation.display_calls == 0 && conversation.stops == 0);
    conversation.foreground = false;
    conversation.handle_screen_timeout();
    assert(!conversation.display_on_ && conversation.display_calls == 1);
    for (auto kind : {AppKind::Native, AppKind::Runtime}) {
        System s; s.app = AppInfo{{kind, true, "sample"}};
        s.handle_screen_timeout();
        const bool selected = kind == AppKind::Native ? EXPECT_NATIVE : EXPECT_RUNTIME;
        assert(!s.display_on_ && s.stops == int(selected));
        s.handle_screen_timeout(); assert(s.display_calls == 1); // One automatic transition.
    }
    System invalid; invalid.app = AppInfo{{AppKind::Native, false, "hidden"}};
    invalid.handle_screen_timeout(); assert(invalid.stops == 0);
    System missing; missing.handle_screen_timeout(); assert(missing.stops == 0);
    System no_resume; no_resume.resume_app_id_ = INVALID_APP_ID;
    no_resume.app = AppInfo{{AppKind::Native, true, "native"}};
    no_resume.handle_screen_timeout(); assert(no_resume.stops == 0);
    System display_failure; display_failure.display_ok = false;
    display_failure.app = AppInfo{{AppKind::Native, true, "native"}};
    display_failure.handle_screen_timeout(); assert(display_failure.stops == 0 && display_failure.display_on_);
    System stopping; stopping.stopping_ = true;
    stopping.handle_screen_timeout(); assert(stopping.display_calls == 0 && stopping.stops == 0);
    System failed_stop; failed_stop.stop_ok = false;
    failed_stop.app = AppInfo{{AppKind::Runtime, true, "runtime"}};
    failed_stop.handle_screen_timeout(); assert(failed_stop.stops == EXPECT_RUNTIME);
}
'''

class ReclaimTimeoutTest(unittest.TestCase):
    def test_normal_native_runtime_and_legacy_configurations(self):
        for native, runtime, legacy in [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 1)]:
            with self.subTest(native=native, runtime=runtime, legacy=legacy), tempfile.TemporaryDirectory(prefix='espocket-reclaim-') as directory:
                root = Path(directory)
                (root / 'espocket').mkdir()
                (root / 'espocket/system.hpp').write_text(STUB)
                (root / 'sdkconfig.h').write_text('')
                (root / 'esp_log.h').write_text('#pragma once\n#define ESP_LOGW(...) (void)0\n#define ESP_LOGE(...) (void)0\n#define ESP_LOGI(...) (void)0\n')
                (root / 'test.cpp').write_text(TEST)
                binary = root / 'test'
                subprocess.run([
                    os.environ.get('CXX', 'clang++'), '-std=c++23', '-I', str(root),
                    f'-DCONFIG_ESPOCKET_M8_RECLAIM_NATIVE_TEST={native}',
                    f'-DCONFIG_ESPOCKET_M8_RECLAIM_RUNTIME_TEST={runtime}',
                    f'-DCONFIG_ESPOCKET_M6_RECLAIM_ON_TIMEOUT_TEST={legacy}',
                    f'-DEXPECT_NATIVE={int(bool(native or legacy))}',
                    f'-DEXPECT_RUNTIME={int(bool(runtime or legacy))}',
                    str(COMPONENT / 'src/system_timeout.cpp'), str(root / 'test.cpp'), '-o', str(binary),
                ], check=True)
                subprocess.run([str(binary)], check=True)

if __name__ == '__main__':
    unittest.main()
