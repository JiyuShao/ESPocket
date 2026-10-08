"""Exercise actual wake word enumeration and speech model ownership."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class WakeWordModelReferenceTest(unittest.TestCase):
    def test_balanced_model_reference(self):
        with tempfile.TemporaryDirectory(prefix='wake-model-ref-') as directory:
            temporary = Path(directory)
            component = prepare(ROOT / 'firmware/managed_components/espressif__brookesia_hal_adaptor',
                                ROOT / 'firmware/patches/espressif__brookesia_hal_adaptor/0.8.4/manifest.json',
                                temporary / 'component')
            source = (component / 'src/audio/processor_impl.cpp').read_text()
            start = source.index('std::vector<std::string> AudioProcessorCore::get_afe_wake_words()')
            method = source[start:source.index('\n}\n', start) + 3]
            code = r'''
#include <cassert>
#include <cstring>
#include <cstdlib>
#include <functional>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS()
#define BROOKESIA_LOGE(...)
#define BROOKESIA_CHECK_NULL_EXIT(value, ...) if(!(value))return;
#define BROOKESIA_THREAD_CONFIG_GUARD(...)
#define BROOKESIA_CHECK_EXCEPTION_RETURN(action, fallback, ...) action;
namespace lib_utils {
struct FunctionGuard {std::function<void()>action;~FunctionGuard(){action();}};
struct ThreadConfig {static bool check_stack_cache_safe(){return true;}};
}
namespace boost {struct thread {template<class Callable>thread(Callable action){action();}void join(){}};}
constexpr int GET_WAKE_WORDS_THREAD_STACK_SIZE=1024;
struct Models {size_t num=2;const char*model_name[2]={"valid","invalid"};} models;
int references=0, releases=0;
bool null_model=false, throw_words=false;
Models* esp_srmodel_init(const char*){if(null_model)return nullptr;references++;return &models;}
void esp_srmodel_deinit_with_refcount(Models*){assert(references>0);references--;releases++;}
char* esp_srmodel_get_wake_words(Models*,const char*name){
    if(throw_words)throw std::runtime_error("words failure");
    return std::string(name)=="valid"?strdup(" first ; second "):nullptr;
}
void* get_static_srmodels(){return nullptr;}
struct AudioProcessorCore {
    struct WakeConfig {std::string model_partition_label="model";};
    struct Config {struct Afe {std::optional<WakeConfig>wakenet=WakeConfig{};}afe;}config_;
    std::vector<std::string>get_afe_wake_words();
};
''' + method + r'''
int main(){
    AudioProcessorCore core;
    assert((core.get_afe_wake_words()==std::vector<std::string>{"first","second"}));
    assert(references==0&&releases==1);
    references=1;
    for(int iteration=0;iteration<100;iteration++){
        core.get_afe_wake_words();assert(references==1);
    }
    references=0;null_model=true;int prior=releases;
    assert(core.get_afe_wake_words().empty());assert(references==0&&releases==prior);
    null_model=false;throw_words=true;
    try{core.get_afe_wake_words();assert(false);}catch(const std::runtime_error&){}
    assert(references==0&&releases==prior+1);
    throw_words=false;core.config_.afe.wakenet.reset();
    assert(core.get_afe_wake_words().empty());assert(references==0);
    core.config_.afe.wakenet=AudioProcessorCore::WakeConfig{""};
    assert(core.get_afe_wake_words().empty());assert(references==0);
}
'''
            (temporary / 'main.cpp').write_text(code)
            subprocess.run([os.environ.get('CXX', 'c++'), '-std=c++23', str(temporary / 'main.cpp'),
                            '-o', str(temporary / 'test')], check=True)
            subprocess.run([str(temporary / 'test')], check=True, timeout=10)


if __name__ == '__main__':
    unittest.main()
