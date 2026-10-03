"""Execute the actual Native hearing fixture against its public Storage/Audio seam."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]


class AudioProbeFixtureTest(unittest.TestCase):
    def test_owner_io_unknown_files_and_stop_failure(self):
        with tempfile.TemporaryDirectory(prefix='espocket-audio-fixture-') as directory:
            temp = Path(directory)
            helper = temp / 'brookesia/service_helper/system'
            helper.mkdir(parents=True)
            (helper.parent / 'media').mkdir()
            (temp / 'stub.hpp').write_text(STUB)
            for path in [helper / 'storage.hpp', helper.parent / 'media/audio.hpp']:
                path.write_text('#include "stub.hpp"\n')
            (temp / 'esp_log.h').write_text('#pragma once\n#define ESP_LOGI(...) ((void)0)\n#define ESP_LOGE(...) ((void)0)\n')
            fixture = ROOT / 'firmware/test/device/fixtures/audio_playback_probe.hpp'
            (temp / 'main.cpp').write_text('#include "' + str(fixture) + '"\n' + TEST)
            binary = temp / 'test'
            compiled = subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-I', str(temp),
                            str(temp / 'main.cpp'), '-o', str(binary)], capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            subprocess.run([str(binary)], check=True, capture_output=True, text=True)


STUB = r'''
#pragma once
#include <expected>
#include <string>
#include <map>
#include <variant>
#include <cassert>
#include <cstddef>
namespace boost::json {
struct value {template<class T> value(T) {}};
struct object {object(std::initializer_list<std::pair<const char *, value>>) {}};
}
namespace esp_brookesia::service {
struct RawBuffer {const unsigned char *data; size_t size; RawBuffer(const unsigned char *p,size_t n):data(p),size(n){}};
using EventItemMap=std::map<std::string,std::variant<std::string>>;
struct EventRegistry {struct SignalConnection {bool active=true; bool connected()const{return active;} void disconnect(){active=false;}};};
namespace helper {
struct Timeout {explicit Timeout(int){}};
inline bool exists=false, fail_write=false, fail_remove=false, fail_play=false, fail_stop=false;
inline int writes=0, removes=0, plays=0, stops=0;
struct Storage {
 struct FileInfo {bool exists;};
 static std::expected<FileInfo,std::string> fs_stat(const std::string &,int){return FileInfo{helper::exists};}
 static std::expected<void,std::string> fs_write(const std::string &,const RawBuffer &buffer,int){
  assert(!exists);assert(buffer.size==4);++writes;exists=true;
  if(fail_write)return std::unexpected("partial write");return {};
 }
 static std::expected<void,std::string> fs_remove(const std::string &,int){
  ++removes;if(fail_remove)return std::unexpected("remove denied");exists=false;return {};
 }
};
struct AudioPlayback {
 enum class FunctionId {Play,Stop}; enum class EventId {PlayStateChanged};
 template<class Callback>static EventRegistry::SignalConnection subscribe_event(EventId,Callback){return {};}
 template<class...Args>static std::expected<void,std::string> call_function_sync(FunctionId id,Args&&...){
  if(id==FunctionId::Play){++plays;if(fail_play)return std::unexpected("play failure");}
  else {++stops;if(fail_stop)return std::unexpected("stop failure");} return {};
 }
};
}}
'''

TEST = r'''
#ifdef __APPLE__
#define PROBE_SECTION ".section __TEXT,__const\n"
#define PROBE_SECTION_END ".text\n"
#else
#define PROBE_SECTION ".pushsection .rodata\n"
#define PROBE_SECTION_END ".popsection\n"
#endif
asm(PROBE_SECTION ".global _binary_espocket_audio_probe_wav_start\n"
    "_binary_espocket_audio_probe_wav_start:\n.byte 0x52,0x49,0x46,0x46\n"
    ".global _binary_espocket_audio_probe_wav_end\n_binary_espocket_audio_probe_wav_end:\n" PROBE_SECTION_END);
int main(){
 namespace helper=esp_brookesia::service::helper;
 namespace probe=espocket::audio_probe;
 // Existing data is neither replaced nor removed.
 helper::exists=true;
 assert(!probe::start());assert(helper::writes==0);assert(helper::removes==0);assert(helper::plays==0);
 helper::exists=false;
 assert(probe::start());assert(helper::writes==1);assert(helper::plays==1);assert(probe::owns_file);
 // Failed Stop retains ownership and file; no destructive cleanup before Owner acknowledgment.
 helper::fail_stop=true;
 assert(!probe::stop());assert(helper::exists);assert(probe::owns_file);assert(helper::removes==0);
 assert(!probe::start());assert(helper::writes==1);
 helper::fail_stop=false;
 assert(probe::stop());assert(!helper::exists);assert(!probe::owns_file);assert(helper::removes==1);
 assert(probe::stop());assert(helper::removes==1);
 // A partial fixture write is cleaned through the Storage Owner without submitting playback.
 helper::fail_write=true;
 assert(!probe::start());assert(!helper::exists);assert(!probe::owns_file);assert(helper::plays==1);
 helper::fail_write=false;helper::fail_play=true;
 assert(!probe::start());assert(!helper::exists);assert(!probe::owns_file);
 helper::fail_play=false;
 assert(probe::start());helper::fail_remove=true;
 assert(!probe::stop());assert(helper::exists);assert(probe::owns_file);
 helper::fail_remove=false;
 assert(probe::stop());assert(!helper::exists);assert(!probe::owns_file);
}
'''
