"""Exercise real timer metrics with independent wake/queue/logic delays."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[3]

class RuntimeTimerProfileTest(unittest.TestCase):
    def test_real_probe_keeps_lateness_and_callback_time_separate(self):
        sys.path.insert(0,str(ROOT/'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='espocket-timer-profile-') as directory:
            root=Path(directory)
            core=prepare(ROOT/'firmware/managed_components/espressif__brookesia_system_core',ROOT/'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json',root/'core')
            source=(core/'src/system/timer.cpp').read_text()
            actual=source[source.index('struct TimerProbe {'):source.index('\n}\n#endif',source.index('struct TimerProbe {'))]
            harness=r'''
#include <string_view>
#include <chrono>
#include <atomic>
#include <algorithm>
#include <cstdint>
#include <cassert>
using AppId=uint32_t;
int64_t timer_probe_now(){return 0;}
unsigned logs=0;
template<class...Args>void log_sample(const char*,Args&&...){++logs;}
#define BROOKESIA_LOGI(...) log_sample(__VA_ARGS__)
'''+actual+r'''
int main(){
 TimerProbe p{};p.enabled=true;p.interval_us=20000;
 p.record(1,"game",100,50,500,650);
 p.record(1,"game",800,70,1000,1020);
 assert(p.callbacks==2 && p.wake_us==120 && p.wake_max_us==70);
 assert(p.queue_us==600 && p.queue_max_us==400);
 assert(p.callback_us==170 && p.callback_max_us==150);
 assert(p.periods==1 && p.period_us==500 && p.period_max_us==500 && !logs);
 ++p.coalesced;p.record(1,"game",1999000,0,2000000,2000010);
 assert(logs==1 && !p.callbacks && !p.queue_us && !p.callback_us && !p.coalesced.load());
 p.enabled=false;p.record(1,"native",0,10000,9000000,9900000);assert(logs==1 && !p.callbacks);
}
'''
            src=root/'main.cpp';src.write_text(harness);binary=root/'test'
            compiled=subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23',str(src),'-o',str(binary)],capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
