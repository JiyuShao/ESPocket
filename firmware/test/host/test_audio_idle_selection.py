"""Execute the real Audio Owner selection method, including busy-output exclusion."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class AudioIdleSelectionTest(unittest.TestCase):
    def test_busy_output_has_no_side_effect_and_normal_selection_still_preempts(self):
        with tempfile.TemporaryDirectory(prefix='audio-idle-selection-') as d:
            work = Path(d)
            audio = prepare(ROOT / 'firmware/managed_components/espressif__brookesia_service_audio',
                            ROOT / 'firmware/patches/espressif__brookesia_service_audio/0.8.2/manifest.json', work / 'audio')
            text = (audio / 'src/audio_decoder.cpp').read_text()
            begin = text.index('std::expected<void, std::string> AudioDecoder::set_active_source(')
            method = text[begin:text.index('std::expected<std::string, std::string> AudioDecoder::get_active_source(', begin)]
            cpp = work / 'test.cpp'
            cpp.write_text(r'''
#include <cassert>
#include <expected>
#include <map>
#include <mutex>
#include <set>
#include <string>
#include <string_view>
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS()
enum class AudioSourceState{Requested,Granted};
struct AudioDecoder{
 struct Stream{bool opened=true;};struct Source{struct Info{int id;std::string name;}info;
  std::set<std::string>requested_outputs{"speaker"};std::map<std::string,Stream>streams{{"speaker",{}}};};
 struct Output{struct{std::string name="speaker";}info;int active_source_id=1;}output;
 Source chat{{1,"chat"}},effect{{2,"effect"}};std::mutex decoder_state_mutex_;
 int events=0,stops=0,clears=0,starts=0;
 Output*find_output_locked(std::string_view name){return name=="speaker"?&output:nullptr;}
 Source*find_source_by_name_locked(std::string_view name){return name=="chat"?&chat:name=="effect"?&effect:nullptr;}
 Source*find_source_by_id_locked(int id){return id==1?&chat:id==2?&effect:nullptr;}
 void emit_source_state_changed(auto,auto,auto){++events;}void emit_active_source_changed(auto,auto){++events;}
 void stop_hal_decoder_locked(){++stops;}void clear_all_queues_locked(){++clears;}
 void ensure_hal_decoder_for_active_stream_locked(Source&,auto){++starts;}
 std::expected<void,std::string>set_active_source(std::string_view,std::string_view,bool only_if_idle=false);
};
''' + method + r'''
int main(){
 AudioDecoder decoder;
 assert(!decoder.set_active_source("speaker","effect",true));
 assert(decoder.output.active_source_id==1 && decoder.events==0 && decoder.stops==0 && decoder.clears==0);
 assert(!decoder.set_active_source("missing","effect",true));assert(!decoder.set_active_source("speaker","missing",true));
 decoder.output.active_source_id=0;assert(decoder.set_active_source("speaker","effect",true));
 assert(decoder.output.active_source_id==2 && decoder.events==2 && decoder.starts==1);
 assert(decoder.set_active_source("speaker","effect",true));assert(decoder.events==2); // idempotent
 assert(!decoder.set_active_source("speaker","chat",true));assert(decoder.output.active_source_id==2);
 assert(decoder.set_active_source("speaker","chat"));assert(decoder.output.active_source_id==1); // legacy contract
 decoder.output.active_source_id=0;decoder.effect.requested_outputs.clear();
 assert(!decoder.set_active_source("speaker","effect",true));assert(decoder.output.active_source_id==0);
}
''')
            binary = work / 'test'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread', str(cpp), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=10)
