"""Exercise real output callback with quiet, full-scale, stereo and inactive streams."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class DecoderOutputGainTest(unittest.TestCase):
    def test_actual_output_callback_is_bounded_and_decoder_only(self):
        with tempfile.TemporaryDirectory(prefix='decoder-gain-') as directory:
            temporary = Path(directory)
            component = prepare(ROOT / 'firmware/managed_components/espressif__brookesia_hal_adaptor',
                                ROOT / 'firmware/patches/espressif__brookesia_hal_adaptor/0.8.4/manifest.json',
                                temporary / 'component')
            source = (component / 'src/audio/processor_impl.cpp').read_text()
            start = source.index('    auto player_write_cb =')
            callback = source[start:source.index('    auto recorder_read_cb =', start)]
            code = r'''
#include <cassert>
#include <array>
#include <cmath>
#include <vector>
#include "pcm_gain.hpp"
using namespace esp_brookesia::hal;
constexpr int ESP_OK=0, ESP_FAIL=-1;
#define BROOKESIA_CHECK_NULL_RETURN(value, result, ...) if (!(value)) return result;
struct Player {
    std::vector<uint8_t> written;
    bool write_data(uint8_t*data,int size){written.assign(data,data+size);return true;}
};
struct AudioProcessorCore {
    Player player;
    Player *player_iface_=&player;
    bool active=false;
    uint8_t player_bits_=16;
    struct Config {struct Decoder {uint16_t output_gain_percent=200, output_peak_percent=100;} decoder;} config_;
    bool is_decoder_started()const{return active;}
};
int main(){
''' + callback + r'''
    AudioProcessorCore core;
    std::array<int16_t,8> quiet{0,1000,-1000,2000,-2000,500,-500,0};
    auto original=quiet;
    auto *data=reinterpret_cast<uint8_t*>(quiet.data());
    assert(player_write_cb(data,sizeof(quiet),&core)==ESP_OK && quiet==original);
    core.active=true;core.player_bits_=24;
    assert(player_write_cb(data,sizeof(quiet),&core)==ESP_OK && quiet==original);
    core.player_bits_=16;core.config_.decoder.output_gain_percent=100;
    assert(player_write_cb(data,sizeof(quiet),&core)==ESP_OK && quiet==original);
    core.config_.decoder.output_gain_percent=400;
    assert(player_write_cb(data,sizeof(quiet),&core)==ESP_OK);
    for(size_t index=0;index<quiet.size();++index)assert(quiet[index]==original[index]*4);
    assert(core.player.written.size()==sizeof(quiet));
    std::array<int16_t,6> peaks{32767,-32768,20000,-20000,10000,-10000};
    auto peak_original=peaks;
    assert(player_write_cb(reinterpret_cast<uint8_t*>(peaks.data()),sizeof(peaks),&core)==ESP_OK);
    for(size_t index=0;index<peaks.size();++index){
        assert((peaks[index]>0)==(peak_original[index]>0));
        assert(peaks[index]>=-32767 && peaks[index]<=32767);
    }
    std::array<int16_t,4> transient{32767,1000,-1000,2000};
    assert(player_write_cb(reinterpret_cast<uint8_t*>(transient.data()),sizeof(transient),&core)==ESP_OK);
    assert(transient[1]>0 && transient[2]<0 && transient[3]>transient[1]);
    std::array<int16_t,480> tone{};
    for(size_t index=0;index<tone.size();++index)
        tone[index]=static_cast<int16_t>(20000*std::sin(2*3.141592653589793*index/24));
    const auto clean=tone;
    assert(player_write_cb(reinterpret_cast<uint8_t*>(tone.data()),sizeof(tone),&core)==ESP_OK);
    const auto ratio=static_cast<double>(tone[6])/clean[6];
    for(size_t index=0;index<tone.size();++index)
        assert(std::abs(tone[index]-clean[index]*ratio)<=1.1);
    core.config_.decoder.output_gain_percent=350;
    core.config_.decoder.output_peak_percent=85;
    tone=clean;
    assert(player_write_cb(reinterpret_cast<uint8_t*>(tone.data()),sizeof(tone),&core)==ESP_OK);
    const auto reduced_ratio=static_cast<double>(tone[6])/clean[6];
    assert(tone[6]==32767*85/100);
    for(size_t index=0;index<tone.size();++index){
        assert(std::abs(tone[index])<=32767*85/100);
        assert(std::abs(tone[index]-clean[index]*reduced_ratio)<=1.1);
    }
    std::array<uint8_t,3> odd{255,127,88};auto odd_original=odd;
    assert(player_write_cb(odd.data(),odd.size(),&core)==ESP_OK && odd==odd_original);
    assert(player_write_cb(data,sizeof(quiet),nullptr)==ESP_FAIL);
    apply_bounded_pcm_gain(nullptr,16,200);
    std::array<int16_t,4> silence{};
    apply_bounded_pcm_gain(reinterpret_cast<uint8_t*>(silence.data()),sizeof(silence),200);
    for(auto sample:silence)assert(sample==0);
    int previous=-32768;
    for(int value=-32768;value<=32767;++value){
        int16_t sample=value;
        apply_bounded_pcm_gain(reinterpret_cast<uint8_t*>(&sample),sizeof(sample),400);
        assert(sample>=-32767 && sample<=32767);
        if(value!=0)assert((sample>0)==(value>0));
        assert(sample>=previous);previous=sample;
    }
}
'''
            test = temporary / 'main.cpp'
            test.write_text(code)
            binary = temporary / 'test'
            subprocess.run(['c++', '-std=c++23', '-I', str(component / 'src/audio'), str(test), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
