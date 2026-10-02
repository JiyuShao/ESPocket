"""Execute the actual HAL playback open path with no Recorder interface."""
import os
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[3]
HAL = ROOT / 'firmware/managed_components/espressif__brookesia_hal_adaptor'

class AudioPlaybackOnlyTest(unittest.TestCase):
    def test_playback_can_open_without_enabling_recorder(self):
        sys.path.insert(0, str(ROOT / 'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='espocket-audio-copy-') as directory:
            patched = prepare(HAL, ROOT / 'firmware/patches/espressif__brookesia_hal_adaptor/0.8.4/manifest.json',
                              Path(directory) / 'patched')
            original = self.exercise(HAL)
            self.assertNotEqual(original.returncode, 0)
            self.assertIn('playback-only requires Recorder', original.stderr)
            fixed = self.exercise(patched)
            self.assertEqual(fixed.returncode, 0, fixed.stderr)

    def exercise(self, hal):
        text=(hal/'src/audio/processor_impl.cpp').read_text()
        start=text.index('bool AudioProcessorCore::open_common(')
        end=text.index('void AudioProcessorCore::close_common()',start)
        method=text[start:end]
        harness=r'''
#include <cstdint>
#include <cstring>
#include <functional>
#include <memory>
#include <string>
#include <iostream>
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS()
#define BROOKESIA_LOGW(...)
#define BROOKESIA_LOGE(...)
#define BROOKESIA_DESCRIBE_TO_STR(...) "config"
#define BROOKESIA_CHECK_NULL_RETURN(value,result,...) if (!(value)) return result
#define BROOKESIA_CHECK_FALSE_RETURN(value,result,...) if (!(value)) return result
#define BROOKESIA_CHECK_ESP_ERR_RETURN(value,result,...) if ((value)!=0) return result
#define BROOKESIA_CHECK_ESP_ERR_EXECUTE(value,unused,...) (void)(value)
#define BROOKESIA_CHECK_NULL_EXIT(value,...) if (!(value)) return
constexpr int ESP_OK=0,ESP_FAIL=-1;
using audio_play_state_t=int;
using audio_playback_handle_t=void*;
struct Io { int(*read_cb)(uint8_t*,int,void*)=nullptr; void* read_ctx=nullptr;
    int(*write_cb)(uint8_t*,int,void*)=nullptr; void* write_ctx=nullptr; };
struct audio_manager_config_t { Io play_io,rec_io; char mic_layout[16]; int board_sample_rate,board_bits,board_channels; };
audio_manager_config_t observed_manager;
int audio_manager_init(audio_manager_config_t* c){observed_manager=*c;return 0;}
int audio_manager_deinit(){return 0;}
int audio_playback_open(int*,audio_playback_handle_t* handle){*handle=reinterpret_cast<void*>(1);return 0;}
namespace lib_utils { class FunctionGuard {std::function<void()> cleanup_;public:
    FunctionGuard(std::function<void()> c):cleanup_(c){} ~FunctionGuard(){if(cleanup_)cleanup_();}
    void release(){cleanup_={};}
}; }
struct Format { int bits=16,channels=1,sample_rate=16000; };
int recorder_opens=0;
namespace audio {
struct CodecPlayerIface { Format opened; bool open(Format c){opened=c;return true;} void close(){}
    bool write_data(uint8_t*,int){return true;}
};
struct CodecRecorderIface { struct Info {int bits=16,channels=1,sample_rate=16000;std::string mic_layout;};
    Info get_info(){return {};} bool open(){++recorder_opens;return true;} void close(){}
    bool read_data(uint8_t*,int){return true;}
};
struct PlaybackIface {using EventCallback=std::function<void(int)>;};
}
struct AudioProcessorTypeConverter {static int convert(auto&,const void*,void*){return 0;}};
struct AudioProcessorCore {
    std::shared_ptr<audio::CodecPlayerIface> player_iface_=std::make_shared<audio::CodecPlayerIface>();
    std::shared_ptr<audio::CodecRecorderIface> recorder_iface_;
    struct {struct {Format player;} playback;} config_;
    void* playback_handle_=nullptr;audio::PlaybackIface::EventCallback playback_callback_;bool is_opened_=false;
    void on_recorder_input_data(uint8_t*,int){} void on_playback_event(uint8_t){}
    bool open_common(audio::PlaybackIface::EventCallback);
};
''' + method + r'''
int main(){AudioProcessorCore core;
    if(!core.open_common({})){std::cerr<<"FAIL: playback-only requires Recorder\n";return 1;}
    if(recorder_opens || observed_manager.rec_io.read_cb || observed_manager.rec_io.read_ctx){
        std::cerr<<"FAIL: playback-only opened or wired Recorder\n";return 2;}
    if(!observed_manager.play_io.write_cb || observed_manager.board_sample_rate!=16000 ||
       observed_manager.board_bits!=16 || observed_manager.board_channels!=1)return 3;
    // Existing duplex mode retains recorder normalization and initialization.
    AudioProcessorCore duplex;duplex.recorder_iface_=std::make_shared<audio::CodecRecorderIface>();
    if(!duplex.open_common({}) || recorder_opens!=1 || !observed_manager.rec_io.read_cb)return 4;
}
'''
        with tempfile.TemporaryDirectory(prefix='espocket-audio-only-') as directory:
            source=Path(directory)/'test.cpp';source.write_text(harness)
            binary=Path(directory)/'test'
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23',str(source),'-o',str(binary)],check=True)
            return subprocess.run([str(binary)],text=True,capture_output=True)

    def test_playback_only_does_not_advertise_recording_interface(self):
        sys.path.insert(0, str(ROOT / 'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='espocket-audio-specs-') as directory:
            patched = prepare(HAL, ROOT / 'firmware/patches/espressif__brookesia_hal_adaptor/0.8.4/manifest.json',
                              Path(directory) / 'patched')
            text=(patched/'src/audio/device.cpp').read_text()
            start=text.index('std::vector<InterfaceSpec> AudioDevice::get_interface_specs() const')
            end=text.index('bool AudioDevice::on_init()',start)
            harness=r'''
#include <cassert>
#include <string>
#include <vector>
#define BROOKESIA_HAL_ADAPTOR_AUDIO_ENABLE_CODEC_PLAYER_IMPL 1
#define BROOKESIA_HAL_ADAPTOR_AUDIO_ENABLE_CODEC_RECORDER_IMPL 0
#define BROOKESIA_HAL_ADAPTOR_AUDIO_ENABLE_PROCESSOR_IMPL 1
struct InterfaceSpec {std::string name,implementation;};
namespace audio {
struct CodecPlayerIface {static constexpr const char* NAME="player";};
struct CodecRecorderIface {static constexpr const char* NAME="recorder";};
struct PlaybackIface {static constexpr const char* NAME="playback";};
struct EncoderIface {static constexpr const char* NAME="encoder";};
struct DecoderIface {static constexpr const char* NAME="decoder";};
}
constexpr const char* CODEC_PLAYER_IMPL_NAME="player",*CODEC_RECORDER_IMPL_NAME="recorder",
*PLAYBACK_IMPL_NAME="playback",*ENCODER_IMPL_NAME="encoder",*DECODER_IMPL_NAME="decoder";
struct AudioDevice {std::vector<InterfaceSpec> get_interface_specs() const;};
''' + text[start:end] + r'''
int main(){AudioDevice device;bool playback=false;
for(const auto& spec:device.get_interface_specs()){
assert(spec.name!="recorder" && spec.name!="encoder");
if(spec.name=="playback")playback=true;
} assert(playback);}
'''
            source=Path(directory)/'specs.cpp';source.write_text(harness)
            binary=Path(directory)/'specs'
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23',str(source),'-o',str(binary)],check=True)
            subprocess.run([str(binary)],check=True)
