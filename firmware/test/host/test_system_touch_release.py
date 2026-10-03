"""Exercise real System input arbitration with a release-triggered App launch."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
COMPONENT = ROOT / 'firmware/components/espocket_test_adapter'


class SystemTouchReleaseTest(unittest.TestCase):
    def test_launched_app_does_not_recancel_delivered_release(self):
        source = (ROOT / 'firmware/components/espocket_system/src/system_test_input.cpp').read_text()
        actual = source[source.index('std::expected<void, std::string> System::tick_test_touch()'):source.index('std::expected<void, std::string> System::release_test_input()')]
        harness = r'''
#include <atomic>
#include <cassert>
#include <cstdio>
#include <memory>
#include "espocket/touch_input_sequence.hpp"
uint64_t time_us=0;
uint64_t esp_timer_get_time(){return time_us;}
namespace espocket {
struct Mode {bool enabled(){return true;}};
struct System {
 std::unique_ptr<TouchInputSequence> test_touch_input_;
 std::atomic_bool stopping_=false,display_on_=true,cancel_test_touch_=false;
 Mode mode;Mode* developer_mode_=&mode;
 std::shared_ptr<std::atomic_uint64_t> foreground_token_=std::make_shared<std::atomic_uint64_t>(0);
 uint64_t test_touch_foreground_token_=0;
 std::expected<void,std::string> tick_test_touch();
};
''' + actual + r'''
}
int main(){
 using namespace espocket; TestInputQueue queue; System system;bool cancelled=false;unsigned cleaned=0;
 system.test_touch_input_=std::make_unique<TouchInputSequence>(queue,
 [&](const TouchInputStep& point,bool)->std::expected<void,std::string>{
  if(!point.pressed)system.foreground_token_->store(1); return {};},
 [&](bool cancel)->std::expected<void,std::string>{cancelled=cancel;++cleaned;return {};});
 auto start=[&](){system.foreground_token_->store(0);system.cancel_test_touch_=false;time_us=0;
  assert(system.test_touch_input_->start({{233,378,0,true},{233,378,80,false}},466,466,0));
  assert(system.tick_test_touch());};
 start();time_us=80000;assert(system.tick_test_touch());time_us=120000;assert(system.tick_test_touch());
 if(cancelled){fprintf(stderr,"FAIL: completed release recancelled after launching App\n");return 1;}
 assert(cleaned==1 && !queue.busy());
 start();system.foreground_token_->store(1);time_us=40000;assert(system.tick_test_touch());
 assert(cancelled && !queue.busy()); // Remaining points must never enter the new App.
 start();time_us=80000;assert(system.tick_test_touch());system.cancel_test_touch_=true;
 time_us=120000;assert(system.tick_test_touch());assert(cancelled && !queue.busy());
}
'''
        with tempfile.TemporaryDirectory(prefix='espocket-system-release-') as directory:
            path=Path(directory)/'test.cpp';path.write_text(harness);binary=Path(directory)/'test'
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23','-I',str(COMPONENT/'include'),str(path),str(COMPONENT/'src/touch_input_sequence.cpp'),str(COMPONENT/'src/test_input_queue.cpp'),'-o',str(binary)],check=True)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)
