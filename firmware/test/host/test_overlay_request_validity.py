"""Execute read-only validity queries from the hash-verified Core patch."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class OverlayRequestValidityTest(unittest.TestCase):
    def test_real_owner_identity_revocation_and_scheduling_failure(self):
        with tempfile.TemporaryDirectory(prefix='espocket-overlay-owner-') as directory:
            base = Path(directory)
            core = prepare(
                ROOT / 'firmware/managed_components/espressif__brookesia_system_core',
                ROOT / 'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json',
                base / 'core',
            )
            manager = (core / 'src/app/manager.cpp').read_text()
            methods = manager[manager.index('bool System::has_app_keyboard_request('):
                              manager.index('std::expected<void, std::string> System::show_app_loading(')]
            cpp = base / 'test.cpp'
            cpp.write_text(r'''
#include <cassert>
#include <map>
#include <optional>
#include <cstdint>
#include <utility>
using AppId=uint32_t;using KeyboardRequestId=uint64_t;using MessageDialogRequestId=uint64_t;
constexpr int SYSTEM_APP_TASK_GROUP=1;
bool blocking=false;
bool is_blocking_runtime_service_call_context(){return blocking;}
struct Impl {
    struct Request {AppId app_id;};
    std::map<uint64_t,Request> keyboard_requests_,message_dialog_requests_;
    std::optional<uint64_t> active_message_dialog_request_id_;
    bool schedule=false,post_fail=false;int posts=0;
    bool should_schedule_app_task(){return schedule;}
    template<class T,class F>T run_task_sync(int group,F callback,T fallback){
        assert(group==SYSTEM_APP_TASK_GROUP);++posts;
        if(post_fail)return fallback;
        schedule=false;auto result=callback();schedule=true;return result;
    }
};
struct System {
    Impl* impl_;
    bool has_app_keyboard_request(AppId,KeyboardRequestId);
    bool has_message_dialog_request(AppId,MessageDialogRequestId);
};
''' + methods + r'''
int main(){
    Impl impl;System s{&impl};
    assert(!s.has_app_keyboard_request(2,10));
    impl.keyboard_requests_[10]={2};assert(s.has_app_keyboard_request(2,10));
    assert(!s.has_app_keyboard_request(3,10));
    impl.message_dialog_requests_[20]={0};assert(!s.has_message_dialog_request(0,20));
    impl.active_message_dialog_request_id_=20;assert(s.has_message_dialog_request(0,20));
    assert(!s.has_message_dialog_request(2,20));
    impl.schedule=true;assert(s.has_app_keyboard_request(2,10));assert(impl.posts==1);
    impl.post_fail=true;assert(!s.has_app_keyboard_request(2,10));
    assert(!s.has_message_dialog_request(0,20));assert(impl.posts==3);
    // A synchronous Runtime Service strand cannot repost to its blocked App task.
    blocking=true;assert(s.has_app_keyboard_request(2,10));assert(impl.posts==3);
    blocking=false;impl.schedule=false;
    // Deferred/failed GUI hide does not keep a revoked request valid.
    impl.keyboard_requests_.erase(10);impl.message_dialog_requests_.erase(20);
    assert(!s.has_app_keyboard_request(2,10));assert(!s.has_message_dialog_request(0,20));
}
''')
            binary = base / 'test'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23',
                            str(cpp), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=10)
