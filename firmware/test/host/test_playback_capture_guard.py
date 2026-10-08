"""Actual DAC/ADC callbacks must mute speaker echo before AFE, without stopping capture."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class PlaybackCaptureGuardTest(unittest.TestCase):
    def test_output_tail_silence_capture_drain_and_default_disabled(self):
        with tempfile.TemporaryDirectory(prefix='espocket-capture-guard-') as temporary:
            directory = Path(temporary)
            component = 'espressif__brookesia_hal_adaptor'
            prepared = prepare(ROOT / 'firmware/managed_components' / component,
                               ROOT / 'firmware/patches' / component / '0.8.4/manifest.json',
                               directory / 'component')
            source = (prepared / 'src/audio/processor_impl.cpp').read_text()
            callbacks = source[source.index('    auto player_write_cb ='):source.index('    audio_manager_config_t manager_config')]
            cpp = r'''
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <mutex>
#include <thread>
#include <vector>
#if __has_include("playback_capture_guard.hpp")
#include "playback_capture_guard.hpp"
#include "software_aec_reference.hpp"
#else
namespace esp_brookesia::hal {struct PlaybackCaptureGuard {void configure(int,int,int,int){}void note_output(uint8_t*,int,int64_t){}bool suppresses_capture(int64_t){return false;}};}
#endif
using namespace esp_brookesia::hal;
constexpr int ESP_OK=0, ESP_FAIL=-1;
#define BROOKESIA_CHECK_NULL_RETURN(v,r,...) if(!(v)) return r
int64_t now_us=1000000;
int64_t esp_timer_get_time(){return now_us;}
struct Player {bool success=true; bool write_data(uint8_t*,int){return success;}};
struct Recorder {int reads=0; bool read_data(uint8_t*data,int size){++reads;std::memset(data,0x22,size);return true;}};
struct Gain {bool process(uint8_t*,size_t){return true;}};
struct AudioProcessorCore {
 Player player;Player*player_iface_=&player;Recorder recorder;Recorder*recorder_iface_=&recorder;
 bool started=true;std::mutex decoder_output_mutex_;Gain decoder_output_gain_;
 PlaybackCaptureGuard playback_capture_guard_;
 SoftwareAecReference software_aec_reference_;
 bool is_decoder_started(){return started;}
 int nonzero_observations=0;
 void on_recorder_input_data(uint8_t*data,int size){for(int i=0;i<size;i++)if(data[i]){++nonzero_observations;break;}}
};
int main(){
''' + callbacks + r'''
 AudioProcessorCore core;
 std::array<int16_t,320> speaker; speaker.fill(2000);
 std::array<uint8_t,1024> mic;
 // Opt-in only. Existing realtime users retain capture while playing.
 assert(player_write_cb(reinterpret_cast<uint8_t*>(speaker.data()),sizeof(speaker),&core)==ESP_OK);
 assert(recorder_read_cb(mic.data(),mic.size(),&core)==ESP_OK && mic[0]!=0);
 core.playback_capture_guard_.configure(16000,2,16,250);
 assert(player_write_cb(reinterpret_cast<uint8_t*>(speaker.data()),sizeof(speaker),&core)==ESP_OK);
 assert(recorder_read_cb(mic.data(),mic.size(),&core)==ESP_OK && mic[0]==0);
 assert(core.recorder.reads==2 && core.nonzero_observations==1);
 // A network stop does not end suppression; actual PCM continues to extend it.
 now_us+=200000;
 assert(player_write_cb(reinterpret_cast<uint8_t*>(speaker.data()),sizeof(speaker),&core)==ESP_OK);
 now_us+=200000;
 assert(recorder_read_cb(mic.data(),mic.size(),&core)==ESP_OK && mic[0]==0);
 std::array<int16_t,320> silence{};
 assert(player_write_cb(reinterpret_cast<uint8_t*>(silence.data()),sizeof(silence),&core)==ESP_OK);
 now_us+=70000;
 assert(recorder_read_cb(mic.data(),mic.size(),&core)==ESP_OK && mic[0]!=0);
 // Continuous idle/silent mixer callbacks must not permanently suppress wake words.
 for(int i=0;i<100;i++){now_us+=10000;player_write_cb(reinterpret_cast<uint8_t*>(silence.data()),sizeof(silence),&core);}
 assert(recorder_read_cb(mic.data(),mic.size(),&core)==ESP_OK && mic[0]!=0);
 // Reset and lifecycle reconfiguration revoke an old suppression window.
 core.playback_capture_guard_.configure(16000,2,16,0);
 assert(recorder_read_cb(mic.data(),mic.size(),&core)==ESP_OK && mic[0]!=0);
 // Candidate callbacks preserve the live microphone and add actual left DAC PCM.
 assert(core.software_aec_reference_.configure(true,16000,2,16,0));
 std::array<int16_t,512> reference_output;reference_output.fill(2000);
 assert(player_write_cb(reinterpret_cast<uint8_t*>(reference_output.data()),sizeof(reference_output),&core)==ESP_OK);
 now_us+=16000;
 assert(recorder_read_cb(mic.data(),mic.size(),&core)==ESP_OK);
 for(size_t frame=0;frame<mic.size()/4;frame++){
  int16_t near_end,reference;
  std::memcpy(&near_end,mic.data()+frame*4,2);std::memcpy(&reference,mic.data()+frame*4+2,2);
  assert(near_end==0x2222 && reference==2000);
 }
 core.player.success=false;
 assert(player_write_cb(reinterpret_cast<uint8_t*>(reference_output.data()),sizeof(reference_output),&core)==ESP_FAIL);
 now_us+=16000;
 assert(recorder_read_cb(mic.data(),mic.size(),&core)==ESP_OK);
 for(size_t frame=0;frame<mic.size()/4;frame++)assert(mic[frame*4+2]==0 && mic[frame*4+3]==0);
 // Concurrent output cannot shorten a later guard.
 PlaybackCaptureGuard guard;guard.configure(16000,2,16,250);
 std::thread late([&]{guard.note_output(reinterpret_cast<uint8_t*>(speaker.data()),sizeof(speaker),3000000);});
 std::thread early([&]{guard.note_output(reinterpret_cast<uint8_t*>(speaker.data()),sizeof(speaker),2000000);});
 late.join();early.join();assert(guard.suppresses_capture(3200000));assert(!guard.suppresses_capture(3300000));
}
'''
            path = directory / 'test.cpp'
            path.write_text(cpp)
            binary = directory / 'test'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++20', '-pthread',
                            '-I', str(prepared / 'src/audio'), str(path), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
