"""Exercise actual PCM output, arbitrary frame partitioning and decoder teardown."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class DecoderOutputGainTest(unittest.TestCase):
    def test_stream_continuity_partitioning_and_lifecycle(self):
        with tempfile.TemporaryDirectory(prefix='decoder-gain-') as directory:
            temporary = Path(directory)
            component = prepare(ROOT / 'firmware/managed_components/espressif__brookesia_hal_adaptor',
                                ROOT / 'firmware/patches/espressif__brookesia_hal_adaptor/0.8.4/manifest.json',
                                temporary / 'component')
            source = (component / 'src/audio/processor_impl.cpp').read_text()
            start = source.index('    auto player_write_cb =')
            callback = source[start:source.index('    auto recorder_read_cb =', start)]
            start = source.index('bool AudioProcessorCore::start_decoder(')
            lifecycle = source[start:source.index('bool AudioProcessorCore::feed_decoder_data(', start)]
            code = r'''
#include <cassert>
#include <cmath>
#include <cstdio>
#include <functional>
#include <mutex>
#include <random>
#include <thread>
#include <vector>
#include "pcm_gain.hpp"
#include "playback_capture_guard.hpp"
#include "software_aec_reference.hpp"
using namespace esp_brookesia::hal;
int64_t esp_timer_get_time(){return 1000000;}
constexpr int ESP_OK=0, ESP_FAIL=-1;
#define BROOKESIA_CHECK_NULL_RETURN(value, result, ...) if (!(value)) return result;
#define BROOKESIA_CHECK_FALSE_RETURN(value, result, ...) if (!(value)) return result;
#define BROOKESIA_CHECK_ESP_ERR_RETURN(value, result, ...) if ((value)!=ESP_OK) return result;
#define BROOKESIA_CHECK_ESP_ERR_EXECUTE(value, unused, ...) (void)(value);
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS()
#define BROOKESIA_LOGD(...)
#define BROOKESIA_LOGE(...)
namespace lib_utils {
struct FunctionGuard {
    std::function<void()> cleanup;
    FunctionGuard(std::function<void()> action):cleanup(action){}
    ~FunctionGuard(){if(cleanup)cleanup();}
    void release(){cleanup={};}
};
}
namespace audio {struct DecoderDynamicConfig {};}
using audio_feeder_handle_t=void*;
bool fail_start=false, fail_mixer=false;
int references=0;
std::vector<int> order;
std::function<void()> first_write, last_write;
int audio_feeder_open(int*,void**handle){*handle=reinterpret_cast<void*>(1);return ESP_OK;}
int audio_feeder_start(void*){if(fail_start)return ESP_FAIL;if(first_write)first_write();return ESP_OK;}
int audio_feeder_close(void*){order.push_back(1);return ESP_OK;}
int audio_processor_mixer_open(void*,void*){return fail_mixer?ESP_FAIL:ESP_OK;}
int audio_processor_mixer_close(){if(last_write)last_write();order.push_back(2);return ESP_OK;}
struct AudioProcessorTypeConverter {
    static int convert(auto&,const audio::DecoderDynamicConfig&){return 0;}
    static void* to_feeder_handle(void*handle){return handle;}
    static void* to_playback_handle(void*handle){return handle;}
};
struct Player {
    std::vector<int16_t> written;
    bool success=true;
    bool write_data(uint8_t*data,int size){
        const auto count=written.size();written.resize(count+size/2);
        std::memcpy(written.data()+count,data,size);return success;
    }
};
struct AudioProcessorCore {
    Player player;
    Player *player_iface_=&player;
    bool is_decoder_started_=false;
    std::mutex decoder_output_mutex_;
    BoundedPcmGain decoder_output_gain_;
    PlaybackCaptureGuard playback_capture_guard_;
 SoftwareAecReference software_aec_reference_;
    struct Config {struct Decoder {} decoder;} config_;
    void *feeder_handle_=nullptr,*playback_handle_=nullptr;
    bool is_decoder_started()const{return is_decoder_started_;}
    bool acquire(){++references;return true;}
    void release(){--references;order.push_back(3);}
    bool start_decoder(const audio::DecoderDynamicConfig&);
    void stop_decoder();
};
''' + lifecycle + r'''
int main(){
''' + callback + r'''
    auto render=[&](const std::vector<int16_t>&input,uint32_t rate,uint8_t channels,
                    uint16_t gain,uint16_t peak,bool split){
        AudioProcessorCore core;
        core.decoder_output_gain_.configure(rate,channels,16,gain,peak);
        assert(core.start_decoder({}));
        std::mt19937 random(93847);
        for(size_t offset=0;offset<input.size();){
            const auto count=std::min(input.size()-offset,split?(1+random()%241)*channels:input.size());
            std::vector<int16_t> block(input.begin()+offset,input.begin()+offset+count);
            assert(player_write_cb(reinterpret_cast<uint8_t*>(block.data()),block.size()*2,&core)==ESP_OK);
            offset+=count;
        }
        core.stop_decoder();
        return core.player.written;
    };
    AudioProcessorCore core;
    core.decoder_output_gain_.configure(16000,1,16,350,85);
    std::array<int16_t,4> quiet{1000,-1000,2000,-2000};auto original=quiet;
    auto*data=reinterpret_cast<uint8_t*>(quiet.data());
    assert(player_write_cb(data,sizeof(quiet),&core)==ESP_OK && quiet==original);
    core.is_decoder_started_=true;
    for(auto bits:{16,24}){
        core.decoder_output_gain_.configure(16000,1,bits,100,100);
        assert(player_write_cb(data,sizeof(quiet),&core)==ESP_OK && quiet==original);
    }
    core.decoder_output_gain_.configure(16000,1,16,350,85);
    std::array<uint8_t,3> odd{255,127,88};auto odd_original=odd;
    assert(player_write_cb(odd.data(),odd.size(),&core)==ESP_FAIL && odd==odd_original);
    assert(player_write_cb(data,sizeof(quiet),nullptr)==ESP_FAIL);
    core.player.success=false;
    assert(player_write_cb(data,sizeof(quiet),&core)==ESP_FAIL);
    std::vector<int16_t> continuous(2000);
    for(size_t index=0;index<continuous.size();++index)
        continuous[index]=static_cast<int16_t>(4000*std::sin(2*3.141592653589793*index/256));
    continuous[580]=32000;
    auto contiguous=render(continuous,16000,1,350,85,false);
    assert(contiguous==render(continuous,16000,1,350,85,true));
    const auto boundary=480+80;
    assert(std::abs(contiguous[boundary]-contiguous[boundary-1])<=
           std::abs(continuous[480]-continuous[479])*4+50);
    for(size_t index=81;index<continuous.size();++index){
        if(index-80==580 || index-81==580)continue;
        const auto natural=std::abs(continuous[index-80]-continuous[index-81]);
        assert(std::abs(contiguous[index]-contiguous[index-1])<=natural*4+180);
    }
    std::vector<int16_t> quiet_stream(1200,1000);
    const auto boosted=render(quiet_stream,16000,1,400,100,true);
    for(size_t index=0;index<80;++index)assert(boosted[index]==0);
    for(size_t index=80;index<quiet_stream.size();++index)assert(boosted[index]==4000);
    assert(boosted.size()==quiet_stream.size()+80 && boosted.back()==0);
    assert(boosted[quiet_stream.size()]>3900);
    assert(render(quiet_stream,16000,1,100,100,true)==quiet_stream);
    for(auto rate:{8000,16000,44100,48000})for(auto channels:{1,2}){
        std::vector<int16_t> input(12000*channels);
        std::mt19937 random(7819);
        for(auto &sample:input)sample=static_cast<int16_t>(random());
        for(auto gain:{0,50,100,350,65535})for(auto peak:{0,85,100}){
            const auto whole=render(input,rate,channels,gain,peak,false);
            assert(whole==render(input,rate,channels,gain,peak,true));
            const auto limit=32767*peak/100;
            for(size_t index=0;index<whole.size();++index){
                const auto sample=whole[index];
                if(std::abs(static_cast<int32_t>(sample))>limit && !(gain==100 && peak==100)){
                    std::fprintf(stderr,"peak: rate=%d channels=%d gain=%d peak=%d index=%zu value=%d\n",
                                 rate,channels,gain,peak,index,sample);
                    assert(false);
                }
            }
        }
    }
    std::vector<int16_t> tone(8000);
    for(size_t index=0;index<tone.size();++index)
        tone[index]=static_cast<int16_t>(20000*std::sin(2*3.141592653589793*index/24));
    auto stable=render(tone,16000,1,350,85,true);
    const auto ratio=(32767*85/100)/20000.0;
    for(size_t index=2000;index<tone.size();++index)
        assert(std::abs(stable[index]-tone[index-80]*ratio)<2);
    std::vector<int16_t> stereo(4000);
    for(size_t index=0;index<stereo.size();index+=2){
        stereo[index]=24000;stereo[index+1]=-12000;
    }
    auto linked=render(stereo,16000,2,350,85,true);
    for(size_t index=160;index<linked.size();index+=2)
        assert(std::abs(linked[index]+2*linked[index+1])<=1);
    AudioProcessorCore lifecycle_core;
    lifecycle_core.decoder_output_gain_.configure(16000,1,16,350,85);
    order.clear();references=0;
    first_write=[&](){
        std::array<int16_t,10> first{};first.fill(1000);
        assert(player_write_cb(reinterpret_cast<uint8_t*>(first.data()),sizeof(first),&lifecycle_core)==ESP_OK);
        for(auto sample:first)assert(sample==0);
    };
    last_write=[&](){
        std::thread worker([&](){
            std::array<int16_t,10> last{};last.fill(1000);
            assert(player_write_cb(reinterpret_cast<uint8_t*>(last.data()),sizeof(last),&lifecycle_core)==ESP_OK);
        });
        worker.join();
    };
    assert(lifecycle_core.start_decoder({}) && references==1);
    assert(lifecycle_core.start_decoder({}) && references==1);
    lifecycle_core.stop_decoder();
    assert(!lifecycle_core.is_decoder_started() && references==0);
    assert((order==std::vector<int>{1,2,3}));
    assert(lifecycle_core.player.written.size()==100 && lifecycle_core.player.written.back()==0);
    lifecycle_core.player.written.clear();
    lifecycle_core.stop_decoder();assert(lifecycle_core.player.written.empty());
    assert(lifecycle_core.start_decoder({}));
    for(auto sample:lifecycle_core.player.written)assert(sample==0);
    lifecycle_core.stop_decoder();
    first_write={};last_write={};
    for(auto mixer_failure:{false,true}){
        fail_mixer=mixer_failure;fail_start=!mixer_failure;
        assert(!lifecycle_core.start_decoder({}) && references==0 && !lifecycle_core.is_decoder_started());
    }
    fail_mixer=false;fail_start=false;
    assert(lifecycle_core.start_decoder({}));lifecycle_core.stop_decoder();
    BoundedPcmGain empty;
    empty.configure(16000,1,16,350,85);
    assert(!empty.process(nullptr,2));
    assert(empty.process(data,0));
    std::array<uint8_t,960> tail{};
    assert(empty.flush(tail.data(),tail.size())==0);
    assert(empty.process(data,sizeof(quiet)));
    assert(empty.flush(tail.data(),1)==0);
    assert(empty.flush(tail.data(),tail.size())==160);
    assert(empty.flush(tail.data(),tail.size())==0);
}
'''
            test = temporary / 'main.cpp'
            test.write_text(code)
            binary = temporary / 'test'
            subprocess.run([os.environ.get('CXX', 'c++'), '-std=c++23', '-fsanitize=undefined,address',
                            '-I', str(component / 'src/audio'), str(test), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=15)


if __name__ == '__main__':
    unittest.main()
