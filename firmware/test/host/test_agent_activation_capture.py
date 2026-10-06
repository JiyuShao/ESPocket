from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class AgentActivationCaptureTest(unittest.TestCase):
    def test_activation_without_capture_and_real_conversation_failure(self):
        with tempfile.TemporaryDirectory(prefix='espocket-agent-activation-') as temporary:
            directory = Path(temporary)
            component = 'espressif__brookesia_agent_manager'
            original = ROOT / 'firmware/managed_components' / component
            prepared = prepare(original, ROOT / 'firmware/patches' / component / '0.8.2/manifest.json', directory / 'component')
            for path, should_activate in ((original, False), (prepared, True)):
                source = (path / 'src/base.cpp').read_text()
                methods = source[source.index('bool Base::on_start()'):source.index('void Base::on_stop()')]
                methods += source[source.index('bool Base::do_activate()'):source.index('void Base::do_stop()')]
                harness = r'''
#include <cassert>
#include <expected>
#include <functional>
#include <memory>
#include <string>
#include <vector>
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS()
#define BROOKESIA_LOGI(...)
#define BROOKESIA_CHECK_NULL_RETURN(value,result,...) if(!(value)) return result
#define BROOKESIA_CHECK_FALSE_RETURN(value,result,...) if(!(value)) return result
struct Scheduler {
    struct Config { int parent_group; };
    bool configure_group(int, Config) { return true; }
};
struct Capture { bool is_available(){return true;} std::vector<std::string> get_afe_wake_words(){return {};}};
int opens=0, activations=0, decodes=0;
bool microphone=false;
namespace df {
enum class Model {AudioCapture};
struct AudioCaptureOperationConfig {std::string owner,provider_id;Model model;int capture;};
}
namespace service {
struct Registry {
    std::expected<std::shared_ptr<Capture>,std::string> open_audio_capture_operation(df::AudioCaptureOperationConfig){
        ++opens;if(!microphone)return std::unexpected("microphone unavailable");return std::make_shared<Capture>();
    }
};
struct ServiceManager {
    static ServiceManager& get_instance(){static ServiceManager manager;return manager;}
    Registry registry; Registry& get_dataflow_registry(){return registry;}
};
}
namespace lib_utils {
struct FunctionGuard {
    std::function<void()> cleanup;
    FunctionGuard(std::function<void()> callback):cleanup(callback){}
    ~FunctionGuard(){if(cleanup)cleanup();}
    void release(){cleanup={};}
};
}
struct Manager { static Manager& get_instance(){static Manager value;return value;} int get_call_task_group(){return 1;} int get_event_task_group(){return 2;} int get_request_task_group(){return 3;} };
constexpr char AGENT_AUDIO_ENCODER_PROVIDER_ID[]="audio.encoder.0";
int to_dataflow_audio_capture_config(int value){return value;}
enum class ChatMode {Manual};
struct Base {
    bool on_start(); bool do_activate(); bool do_start();
    Scheduler scheduler;Scheduler* get_task_scheduler(){return &scheduler;}
    int get_call_task_group(){return 1;}int get_event_task_group(){return 2;}int get_request_task_group(){return 3;}
    struct Attributes {std::string name="XiaoZhi";};Attributes get_attributes(){return {};}
    struct AudioConfig {int encoder=0;}; AudioConfig get_audio_config(){return {};}
    std::shared_ptr<Capture> audio_capture_operation_;
    std::vector<std::string> wake_words_;
    bool on_activate(){++activations;return true;}
    bool start_audio_decoder(){++decodes;return true;}void stop_audio_decoder(){--decodes;}
    bool start_audio_encoder(){return bool(audio_capture_operation_);}void stop_audio_encoder(){}
    void set_encoder_paused(bool){}ChatMode get_chat_mode(){return ChatMode::Manual;}
    bool on_startup(){return true;}void stop(){}
};
''' + methods + '\nint main(){Base base; const bool started=base.on_start(); assert(started==' + str(should_activate).lower() + r''');
if(started){assert(opens==0);assert(base.do_activate());assert(activations==1);assert(!base.do_start());
assert(opens==1 && decodes==0);microphone=true;assert(base.do_start());assert(opens==2);assert(base.do_start());assert(opens==2);}
else{assert(opens==1 && activations==0);}}
'''
                cpp = directory / 'test.cpp'
                binary = directory / 'test'
                cpp.write_text(harness)
                subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(cpp), '-o', str(binary)], check=True)
                subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
