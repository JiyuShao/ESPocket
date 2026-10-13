"""Exercise production PinballApp lifecycle with GUI/timer/audio boundary doubles."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]

def run(code):
    with tempfile.TemporaryDirectory(prefix='pinball-app-test-') as d:
        cpp, binary = Path(d) / 'test.cpp', Path(d) / 'test'
        cpp.write_text(code)
        subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-Wall', '-Wextra', '-I', str(ROOT / 'include'), str(cpp), str(ROOT / 'src/pinball_model.cpp'), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=10)

class PinballAppTest(unittest.TestCase):
    def test_start_pause_resume_stop_and_stale_timer(self):
        source = (ROOT / 'src/pinball_app.cpp').read_text()
        methods = source[source.index('std::expected<void, std::string> PinballApp::on_start('):]
        run(r'''
#include <cassert>
#include <expected>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <vector>
#include "espocket/pinball_model.hpp"
int64_t now=1000000;int64_t esp_timer_get_time(){return now;}
namespace espocket {
struct PinballContent { int paints=0; void paint(const pinball::Model&){++paints;} };
struct ShortEffect { int closes=0,plays=0; explicit ShortEffect(std::string){} void close(){++closes;} void poll(){} void play(unsigned,unsigned){++plays;} };
namespace core {
using TimerId=int;
struct State { uint64_t instance=1; bool paused=false; std::optional<uint64_t>activity_epoch=5; bool suspended()const{return paused;} };
struct System { std::optional<State> state=State{}; int activity=0; auto execution_state(){return state;} void report_user_activity(uint64_t,uint64_t){++activity;} };
struct Frame { bool valid=true,cancelled=false; uint32_t sequence=1; std::vector<pinball::Point>points; };
struct Gui { bool fail_mount=false; int mounts=0,unmounts=0; Frame frame;
 std::expected<int,std::string> mount_native_content(std::string_view,std::shared_ptr<PinballContent>){++mounts;if(fail_mount)return std::unexpected("mount");return 1;}
 void unmount_native_content(int){++unmounts;}
 std::expected<Frame,std::string> read_native_pointer_frame(int){return frame;}
 template<class F>std::expected<void,std::string> invoke_native_content(int,F f){PinballContent c;f(c);return {};}
};
struct Timer { bool fail=false; int next=1,stops=0; std::expected<int,std::string> start_periodic(std::string_view,int){if(fail)return std::unexpected("timer");return next++;} void stop(int){++stops;} };
struct AppContext { System s;Gui g;Timer t;auto&system_service(){return s;}auto&gui(){return g;}auto&timer(){return t;} };
}
struct PinballApp {
 pinball::Model model_; std::shared_ptr<PinballContent>content_; std::unique_ptr<ShortEffect>sound_=std::make_unique<ShortEffect>("test");
 int mount_=0,timer_=0;uint64_t instance_=0;int64_t last_tick_us_=0;bool running_=false,has_frame_=false;uint32_t last_sequence_=0;
 std::expected<void,std::string>on_start(core::AppContext&);std::expected<void,std::string>on_pause(core::AppContext&);std::expected<void,std::string>on_resume(core::AppContext&);std::expected<void,std::string>on_stop(core::AppContext&);std::expected<void,std::string>on_timer(core::AppContext&,int,std::string_view);
};
''' + methods + r'''
int main(){using namespace espocket;core::AppContext c;PinballApp app;
 c.s.state.reset();assert(!app.on_start(c)&&c.g.mounts==0);
 c.s.state=core::State{};c.g.fail_mount=true;assert(!app.on_start(c)&&!app.content_);
 c.g.fail_mount=false;c.t.fail=true;assert(!app.on_start(c)&&c.g.unmounts==1&&!app.content_);
 c.t.fail=false;assert(app.on_start(c));int old=app.timer_;const int start_balls=app.model_.state().balls;
 c.g.frame.points.clear();now+=20000;assert(app.on_timer(c,old,"release"));c.g.frame.sequence++;c.g.frame.points={{233,390,1}};now+=20000;assert(app.on_timer(c,old,"start"));assert(app.model_.state().phase==pinball::Phase::Playing&&c.s.activity==1);
 c.s.state->paused=true;auto before=app.model_.state();now+=100000;assert(app.on_timer(c,old,"covered"));assert(app.model_.state().x==before.x&&app.model_.state().y==before.y);
 assert(app.on_pause(c));assert(!app.model_.state().flippers[0].on);now+=60000000;assert(app.on_timer(c,old,"late"));
 c.s.state->paused=false;assert(app.on_resume(c));now+=20000;c.g.frame.cancelled=true;c.g.frame.points.clear();assert(app.on_timer(c,old,"resume"));assert(app.model_.state().balls==start_balls);
 assert(app.on_stop(c)&&!app.content_&&c.t.stops==1);assert(app.on_timer(c,old,"stale"));assert(app.on_stop(c));
 c.s.state=core::State{.instance=2};assert(app.on_start(c));assert(app.model_.state().phase==pinball::Phase::Ready&&app.model_.state().balls==3);assert(app.on_timer(c,old,"old id"));assert(app.on_stop(c));
}
''')

if __name__ == '__main__': unittest.main()
