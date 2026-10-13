"""Run actual short-effect adapter methods with a fake public Audio Service boundary."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]


class BubbleSoundTest(unittest.TestCase):
    def test_busy_muted_release_lifetime_and_pause_cleanup(self):
        header = (ROOT / 'src/bubble_sound.hpp').read_text()
        body = header[header.index('namespace espocket {'):]
        methods = (ROOT / 'src/bubble_sound.cpp').read_text()
        methods = methods[methods.index('namespace espocket {'):]
        code = r'''
#include <algorithm>
#include <atomic>
#include <cassert>
#include <expected>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <stdexcept>
#include <vector>
int64_t now=1000000;int64_t esp_timer_get_time(){return now;}
namespace esp_brookesia::service {
struct RawBuffer {void*data;size_t size;RawBuffer(void*p,size_t n):data(p),size(n){}};
enum class AudioWriteResult{Written,Error};
struct AudioStreamConfig{struct General{int channels,sample_bits,sample_rate,frame_duration;}general;size_t queue_size_bytes;};
struct ServiceBinding{bool valid=false;bool is_valid(){return valid;}void release(){valid=false;}};
struct ServiceManager{static ServiceManager&get_instance(){static ServiceManager manager;return manager;}ServiceBinding bind(std::string_view){return {true};}};
struct AudioDecoder{
 bool busy=false,fail_open=false,fail_write=false,throw_write=false;int registrations=0,unregisters=0,closes=0,releases=0;
 RawBuffer borrowed{nullptr,0};std::function<void(AudioWriteResult)>completion;
 static AudioDecoder*get_instance(int){static AudioDecoder decoder;return &decoder;}
 struct Output{std::string name="speaker",role="speaker";};std::vector<Output>get_outputs(){return {{}};}
 struct Source{std::string name,role;std::vector<std::string>preferred_outputs;int priority;};
 std::expected<uint32_t,std::string>register_source(Source s){assert(s.priority<0);++registrations;return registrations;}
 std::expected<void,std::string>request_output(uint32_t,std::string_view){return {};}
 std::expected<void,std::string>set_active_source(std::string_view,std::string_view,bool idle){assert(idle);if(busy)return std::unexpected("busy");return {};}
 std::expected<void,std::string>open_stream(uint32_t,std::string_view,const AudioStreamConfig&config){assert(config.queue_size_bytes==12288);if(fail_open)return std::unexpected("open");return {};}
 AudioWriteResult write_stream_borrowed(uint32_t,std::string_view,RawBuffer data,std::function<void(AudioWriteResult)>callback,int timeout){assert(timeout==0);if(throw_write)throw std::bad_alloc{};borrowed=data;completion=callback;if(fail_write){completion(AudioWriteResult::Error);return AudioWriteResult::Error;}return AudioWriteResult::Written;}
 std::expected<void,std::string>close_stream(uint32_t,std::string_view){++closes;if(completion){auto callback=std::move(completion);callback(AudioWriteResult::Error);}return {};}
 std::expected<void,std::string>release_output(uint32_t,std::string_view){++releases;return {};}
 std::expected<void,std::string>unregister_source(uint32_t){++unregisters;return {};}
};
namespace helper {
struct Timeout{Timeout(int){}};
struct AudioPlayback{enum class FunctionId{GetMute};static inline bool available=true;static inline std::optional<bool>muted=false;
 static bool is_available(){return available;}template<class T>static std::expected<T,std::string>call_function_sync(FunctionId,Timeout){if(!muted)return std::unexpected("mute unavailable");return *muted;}
};
}
}
''' + body + methods + r'''
int main(){
 using namespace espocket;using namespace esp_brookesia::service;auto*d=AudioDecoder::get_instance(0);
 using P=helper::AudioPlayback;
 BubbleSound sound;
 P::muted=true;sound.play(1000,22);assert(d->registrations==0);
 P::muted.reset();sound.play(1000,22);assert(d->registrations==0);
 P::muted=false;d->busy=true;sound.play(1000,22);assert(d->registrations==1 && d->unregisters==1 && !d->completion);
 d->busy=false;d->fail_open=true;sound.play(1000,22);assert(d->registrations==2 && d->unregisters==2);
 d->fail_open=false;sound.play(1000,22);assert(d->borrowed.size==22*16*2*2 && d->completion);
 auto*pcm=static_cast<int16_t*>(d->borrowed.data);assert(pcm[0]==5400 && pcm[1]==5400 && pcm[16]==-5400);
 auto before=d->registrations;sound.poll();sound.play(900,22);assert(d->registrations==before); // bounded one in-flight effect
 auto callback=std::move(d->completion);callback(AudioWriteResult::Written);
 sound.poll();assert(d->unregisters==2); // HAL output can still be buffered
 now+=21999;sound.poll();assert(d->unregisters==2);
 ++now;sound.poll();assert(d->unregisters==3);callback={};
 sound.play(520,130);assert(d->borrowed.size==8320);auto late=d->completion;
 sound.close();assert(d->unregisters==4);sound.close();assert(d->unregisters==4);
 sound.play(1000,22);before=d->unregisters;late(AudioWriteResult::Written);
 now+=200000;sound.poll();assert(d->unregisters==before); // previous release cannot close current stream
 sound.close();d->fail_write=true;sound.play(1000,22);assert(d->registrations==d->unregisters);
 d->fail_write=false;d->throw_write=true;sound.play(1000,22);
 assert(d->registrations==d->unregisters); // partial lease is cleaned on allocation exception
}
'''
        with tempfile.TemporaryDirectory(prefix='bubble-sound-') as d:
            cpp, binary = Path(d) / 'test.cpp', Path(d) / 'test'
            cpp.write_text(code)
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(cpp), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=10)


if __name__ == '__main__':
    unittest.main()
