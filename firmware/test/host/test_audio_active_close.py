import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class AudioActiveCloseTest(unittest.TestCase):
    def test_release_can_join_worker_delivering_final_playback_event(self):
        with tempfile.TemporaryDirectory(prefix='espocket-audio-close-') as temporary:
            directory = Path(temporary)
            component = 'espressif__brookesia_hal_adaptor'
            patched = prepare(ROOT / 'firmware/managed_components' / component,
                              ROOT / 'firmware/patches' / component / '0.8.4/manifest.json', directory / 'hal')
            text = (patched / 'src/audio/processor_impl.cpp').read_text()
            methods = text[text.index('void AudioProcessorCore::release()'):text.index('bool AudioProcessorCore::open_common(')]
            methods += text[text.index('void AudioProcessorCore::close_common()'):text.index('bool AudioProcessorCore::play(')]
            methods += text[text.index('void AudioProcessorCore::on_playback_event('):text.index('void AudioProcessorCore::on_recorder_event(')]
            code = r'''
#include <atomic>
#include <cassert>
#include <functional>
#include <memory>
#include <mutex>
#include <thread>
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS()
#define BROOKESIA_LOGE(...)
#define BROOKESIA_CHECK_ESP_ERR_EXECUTE(value,unused,...) (void)(value)
enum audio_play_state_t {AUDIO_PLAY_STATE_IDLE,AUDIO_PLAY_STATE_FINISHED,AUDIO_PLAY_STATE_STOPPED,AUDIO_PLAY_STATE_PLAYING,AUDIO_PLAY_STATE_PAUSED};
namespace audio {enum class PlayState {Idle,Playing,Paused};struct PlaybackIface {using EventCallback=std::function<void(PlayState)>;};}
struct Codec {void close(){}};
int closes=0, events=0;
struct AudioProcessorCore {
    std::mutex mutex_,playback_callback_mutex_;
    size_t open_ref_count_=1;
    audio::PlaybackIface::EventCallback playback_callback_;
    std::atomic_bool is_opened_=true;
    void* playback_handle_=reinterpret_cast<void*>(1);
    std::shared_ptr<Codec> player_iface_=std::make_shared<Codec>(),recorder_iface_;
    void release();void clear_playback_callback();void close_common();void on_playback_event(uint8_t);
};
struct AudioProcessorTypeConverter {static void* to_playback_handle(void* value){return value;}};
AudioProcessorCore* active_core=nullptr;
int audio_playback_close(void*) {
    std::thread worker([]{active_core->on_playback_event(AUDIO_PLAY_STATE_STOPPED);++events;});
    worker.join();++closes;return 0;
}
int audio_manager_deinit(){return 0;}
''' + methods + r'''
int main(){
    AudioProcessorCore core;active_core=&core;
    core.playback_callback_=[](auto){assert(false);};
    core.clear_playback_callback();core.release();
    assert(events==1 && closes==1 && !core.is_opened_ && core.open_ref_count_==0 && !core.playback_handle_);
    core.release();assert(closes==1);
}
'''
            cpp = directory / 'test.cpp'
            binary = directory / 'test'
            cpp.write_text(code)
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread', str(cpp), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=3)


if __name__ == '__main__':
    unittest.main()
