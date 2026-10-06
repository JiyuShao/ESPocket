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
            begin=source.find('template<class Sample>\nvoid log_timer_sample(')
            if begin<0:begin=source.index('struct TimerProbe {')
            actual=source[begin:source.index('\n}\n#endif',source.index('struct TimerProbe {'))]
            harness=r'''
#include <string_view>
#include <chrono>
#include <atomic>
#include <algorithm>
#include <cstdint>
#include <cassert>
#include <deque>
#include <functional>
#include <string>
#define ESP_PLATFORM 1
using UBaseType_t=unsigned;
unsigned worker_priority=10;
UBaseType_t uxTaskPriorityGet(void*){return worker_priority;}
void vTaskPrioritySet(void*,UBaseType_t value){worker_priority=value;}
using AppId=uint32_t;
int64_t timer_probe_now(){return 0;}
unsigned logs=0;
template<class...Args>void log_sample(const char*,Args&&...){assert(worker_priority<=2);++logs;}
#define BROOKESIA_LOGI(...) log_sample(__VA_ARGS__)
'''+actual+r'''
template<class Probe,class Publish>
void record(Probe&p,AppId app,std::string_view name,int64_t enqueued,uint64_t wake,int64_t start,int64_t end,Publish&publish){
 if constexpr(requires{p.record(app,name,enqueued,wake,start,end,publish);})p.record(app,name,enqueued,wake,start,end,publish);
 else p.record(app,name,enqueued,wake,start,end);
}
template<class Probe>void complete(Probe&p){if constexpr(requires{p.sample_pending;})p.sample_pending=false;}
int main(){
 TimerProbe p{};p.enabled=true;p.interval_us=20000;
 std::deque<std::function<void()>> queued;
 auto publish=[&](auto sample){queued.push_back([&,sample=std::move(sample)]{sample();complete(p);});return true;};
 record(p,1,"game",100,50,500,650,publish);
 record(p,1,"game",800,70,1000,1020,publish);
 assert(p.callbacks==2 && p.wake_us==120 && p.wake_max_us==70);
 assert(p.queue_us==600 && p.queue_max_us==400);
 assert(p.callback_us==170 && p.callback_max_us==150);
 assert(p.periods==1 && p.period_us==500 && p.period_max_us==500 && !logs);
 ++p.coalesced;record(p,1,"game",1999000,0,2000000,2000010,publish);
 assert(logs==0 && queued.size()==1 && !p.callbacks && !p.queue_us && !p.callback_us && !p.coalesced.load());
 record(p,1,"game",3999000,0,4000000,4000010,publish);
 assert(logs==0 && queued.size()==1); // Slow serial consumer cannot grow the queue.
 queued.front()();queued.pop_front();assert(logs==1 && worker_priority==10);
 auto reject=[](auto){return false;};record(p,1,"game",5999000,0,6000000,6000010,reject);
 record(p,1,"game",7999000,0,8000000,8000010,publish);
 assert(logs==1 && queued.size()==1); // Failed publication releases the slot.
 queued.front()();queued.pop_front();assert(logs==2 && worker_priority==10);
 p.enabled=false;record(p,1,"native",0,10000,9000000,9900000,publish);assert(logs==2 && !p.callbacks);
}
'''
            src=root/'main.cpp';src.write_text(harness);binary=root/'test'
            compiled=subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23',str(src),'-o',str(binary)],capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
