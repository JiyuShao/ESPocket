"""Check isolated fault injection preserves production and fails on seam drift."""
import importlib.util
from pathlib import Path
import shutil
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('reliability_fixture', ROOT / 'scripts/firmware/prepare_reliability_fixture.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class ReliabilityFixtureTest(unittest.TestCase):
    def copy(self, destination):
        for name in ('main/app_main.cpp', 'components/espocket_system/src/system.cpp'):
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / 'firmware' / name, target)

    def test_modes_are_explicit_and_do_not_change_original_or_preferences(self):
        original = (ROOT / 'firmware/components/espocket_system/src/system.cpp').read_bytes()
        for mode in fixture.MODES:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                project = Path(directory)
                self.copy(project)
                result = fixture.inject(ROOT, project, mode)
                self.assertTrue(result['test_only'])
                self.assertFalse(result['persistent_preferences_modified'])
                main = (project / 'main/app_main.cpp').read_text()
                self.assertIn('"' + mode + '"', main)
                source = (project / 'components/espocket_system/src/system.cpp').read_text()
                if mode != 'lifecycle':
                    self.assertIn('Reliability fixture:' if mode != 'theme-unknown' else 'fixture-unknown', source)
                self.assertNotIn('nvs_set_', source)
                self.assertEqual((ROOT / 'firmware/components/espocket_system/src/system.cpp').read_bytes(), original)

    def test_drift_and_reapplication_rejected_before_mutating_files(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.copy(project)
            main = project / 'main/app_main.cpp'
            source = project / 'components/espocket_system/src/system.cpp'
            source.write_text(source.read_text() + '\n// concurrent drift\n')
            before = main.read_bytes(), source.read_bytes()
            with self.assertRaisesRegex(ValueError, 'unchanged'):
                fixture.inject(ROOT, project, 'theme-unknown')
            self.assertEqual(before, (main.read_bytes(), source.read_bytes()))
            self.copy(project)
            fixture.inject(ROOT, project, 'lifecycle')
            with self.assertRaisesRegex(ValueError, 'unchanged'):
                fixture.inject(ROOT, project, 'lifecycle')

    def test_original_and_unknown_modes_rejected(self):
        with self.assertRaises(ValueError):
            fixture.inject(ROOT, ROOT / 'firmware', 'lifecycle')
        with self.assertRaises(ValueError):
            fixture.inject(ROOT, Path('/private/tmp/unused-project'), 'not-a-mode')

    def test_external_coordinator_accepts_cancellation_but_rejects_retained_requests(self):
        # Test the test coordinator itself, not production System scheduling.
        # Production cleanup is separately exercised by test_core_stop_requests.
        system = r'''
#pragma once
#include <expected>
#include <functional>
#include <optional>
#include <string>
#include <vector>
#include <cstdlib>
namespace esp_brookesia::system::core {
using AppId=unsigned;using KeyboardRequestId=unsigned;using MessageDialogRequestId=unsigned;
enum class AppState { Installed, Stopped, Running };
enum class MessageDialogButtonRole { Action };
struct MessageDialogOptions {std::string text;struct Button {std::string text;MessageDialogButtonRole role;};std::vector<Button> buttons;};
struct KeyboardRequestOptions {};
struct KeyboardResult {bool confirmed;};
struct AppInfo {unsigned app_id;struct Manifest {std::string id;} manifest;AppState state;};
}
namespace espocket {
using namespace esp_brookesia::system::core;
class System {
 std::vector<AppInfo> apps;unsigned active=0,next=1;bool pending=false;
 std::function<void(const KeyboardResult&)> keyboard;
public:
 std::expected<void,std::string> init(){apps={{1,{"espocket.app.hello"},AppState::Installed},{2,{"espocket.app.hello_runtime"},AppState::Installed}};return {};}
 std::expected<void,std::string> start(){return {};}
 auto list_apps(){return apps;}
 std::optional<AppInfo> get_active_app(){for(auto a:apps)if(a.app_id==active)return a;return {};}
 std::expected<void,std::string> start_app(unsigned id){active=id;for(auto& a:apps)if(a.app_id==id)a.state=AppState::Running;return {};}
 void stop(){for(auto& a:apps)a.state=AppState::Stopped;if(keyboard)keyboard({false});if(!std::getenv("RETAIN_OLD_REQUESTS"))pending=false;}
 void deinit(){stop();apps.clear();}
 void report_startup_failure(const std::string&){}
 std::expected<unsigned,std::string> show_app_keyboard(unsigned,KeyboardRequestOptions,std::function<void(const KeyboardResult&)> handler){keyboard=handler;pending=true;return next++;}
 template<class F> std::expected<unsigned,std::string> show_system_message_dialog(MessageDialogOptions,F){return next++;}
 std::expected<void,std::string> complete_app_keyboard(unsigned,unsigned,bool,const std::string&){if(pending)return {};return std::unexpected("revoked");}
 std::expected<void,std::string> hide_system_message_dialog(unsigned){if(pending)return {};return std::unexpected("revoked");}
};
}
'''
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            headers = {
                'espocket/system.hpp': system,
                'esp_heap_caps.h': '#pragma once\n#include <cstddef>\n#define MALLOC_CAP_INTERNAL 1\n#define MALLOC_CAP_SPIRAM 2\ninline size_t heap_caps_get_free_size(int){return 4096;}\ninline size_t heap_caps_get_largest_free_block(int){return 4096;}\n',
                'esp_log.h': '#pragma once\n#include <cstdio>\n#define ESP_LOGI(tag,fmt,...) printf(fmt "\\n",##__VA_ARGS__)\n#define ESP_LOGE ESP_LOGI\n#define ESP_LOGW ESP_LOGI\n',
                'freertos/FreeRTOS.h': '#pragma once\n#define pdMS_TO_TICKS(x) (x)\n',
                'freertos/task.h': '#pragma once\ninline void vTaskDelay(int){}\n',
            }
            for name, contents in headers.items():
                path = project / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(contents)
            entry = (ROOT / 'firmware/test/device/fixtures/reliability/app_main.cpp').read_text()
            cpp = project / 'coordinator.cpp'
            cpp.write_text(entry.replace('RELIABILITY_MODE', 'lifecycle') + '\nint main(){app_main();}\n')
            binary = project / 'coordinator'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-I'+str(project),
                            str(cpp), '-o', str(binary)], check=True)
            environment = dict(os.environ)
            environment.pop('RETAIN_OLD_REQUESTS', None)
            good = subprocess.check_output([str(binary)], env=environment, text=True, timeout=10)
            self.assertIn('SEQUENCE_COMPLETE', good)
            self.assertEqual(good.count('STOP_START_COMPLETE'), 3)
            self.assertEqual(good.count('DEINIT_INIT_COMPLETE'), 3)
            bad = subprocess.check_output([str(binary)], env={**environment, 'RETAIN_OLD_REQUESTS': '1'},
                                          text=True, timeout=10)
            self.assertIn('FAIL old input retained', bad)
            self.assertNotIn('SEQUENCE_COMPLETE', bad)
