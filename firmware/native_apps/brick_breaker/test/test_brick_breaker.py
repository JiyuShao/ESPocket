"""Execute production physics and lifecycle methods; only service boundaries are doubled."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]


def run(code):
    with tempfile.TemporaryDirectory(prefix='brick-breaker-test-') as d:
        cpp, binary = Path(d) / 'test.cpp', Path(d) / 'test'
        cpp.write_text(code)
        subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-Wall', '-Wextra',
                        '-I', str(ROOT / 'include'), str(cpp), str(ROOT / 'src/brick_model.cpp'),
                        '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=10)


class BrickBreakerTest(unittest.TestCase):
    def test_actual_app_pause_stop_start_failure_and_late_timer(self):
        source = (ROOT / 'src/brick_breaker_app.cpp').read_text()
        methods = source[source.index('std::expected<void, std::string> BrickBreakerApp::on_start('):]
        run(r'''
#include <algorithm>
#include <cassert>
#include <expected>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include "espocket/brick_model.hpp"
int64_t now=1000000;int64_t esp_timer_get_time(){return now;}
namespace espocket {
struct BrickContent{int paints=0;void paint(const brick::Model&){++paints;}};
struct ShortEffect{int plays=0,closes=0;void close(){++closes;}void poll(){}void play(unsigned,unsigned){++plays;}};
namespace core {
using TimerId=int;
struct State{uint64_t instance=1;bool paused=false;std::optional<uint64_t>activity_epoch=5;bool suspended()const{return paused;}};
struct System{std::optional<State>state=State{};int activity=0;auto execution_state(){return state;}void report_user_activity(uint64_t,uint64_t){++activity;}};
struct Frame{bool valid=true,cancelled=false;uint32_t sequence=1;std::vector<brick::Point>points;};
struct Gui{
 bool fail_mount=false;int mounts=0,unmounts=0;Frame frame;
 std::expected<int,std::string>mount_native_content(std::string_view,std::shared_ptr<BrickContent>){++mounts;if(fail_mount)return std::unexpected("mount");return 1;}
 void unmount_native_content(int){++unmounts;}
 std::expected<Frame,std::string>read_native_pointer_frame(int){return frame;}
 template<class F>std::expected<void,std::string>invoke_native_content(int,F f){BrickContent content;f(content);return {};}
};
struct Timer{bool fail=false;int next=1,stops=0;std::expected<int,std::string>start_periodic(std::string_view,int){if(fail)return std::unexpected("timer");return next++;}void stop(int){++stops;}};
struct AppContext{System s;Gui g;Timer t;auto&system_service(){return s;}auto&gui(){return g;}auto&timer(){return t;}};
}
struct BrickBreakerApp{
 brick::Model model_;std::shared_ptr<BrickContent>content_;std::unique_ptr<ShortEffect>sound_=std::make_unique<ShortEffect>();
 int mount_=0,timer_=0;uint64_t instance_=0;int64_t last_tick_us_=0;bool running_=false,has_frame_=false;uint32_t last_sequence_=0;
 std::expected<void,std::string>on_start(core::AppContext&);std::expected<void,std::string>on_pause(core::AppContext&);
 std::expected<void,std::string>on_resume(core::AppContext&);std::expected<void,std::string>on_stop(core::AppContext&);
 std::expected<void,std::string>on_timer(core::AppContext&,int,std::string_view);
};
''' + methods + r'''
int main(){
 using namespace espocket;core::AppContext c;BrickBreakerApp app;
 c.s.state.reset();assert(!app.on_start(c));assert(c.g.mounts==0);
 c.s.state=core::State{};c.g.fail_mount=true;assert(!app.on_start(c));assert(!app.content_);
 c.g.fail_mount=false;c.t.fail=true;assert(!app.on_start(c));assert(c.g.unmounts==1 && !app.content_);
 c.t.fail=false;assert(app.on_start(c));int old=app.timer_;const int total=app.model_.state().remaining;
 c.g.frame.points.clear();now+=20000;assert(app.on_timer(c,old,"release"));
 c.g.frame.sequence++;c.g.frame.points={{233,390,1}};
 now+=20000;assert(app.on_timer(c,old,"tick"));assert(app.model_.state().phase==brick::Phase::Playing && c.s.activity==1);
 const auto before=app.model_.state();
 c.s.state->paused=true;now+=20000;assert(app.on_timer(c,old,"covered"));assert(app.model_.state().x==before.x);
 assert(app.on_pause(c));now+=60000000;assert(app.on_timer(c,old,"late"));assert(c.s.activity==1);
 c.g.frame.cancelled=true;c.g.frame.points.clear();c.s.state->paused=false;assert(app.on_resume(c));
 now+=20000;assert(app.on_timer(c,old,"tick"));assert(app.model_.state().remaining==total && app.model_.state().x==before.x+before.vx);
 assert(app.on_stop(c));assert(!app.content_ && c.t.stops==1);assert(app.on_timer(c,old,"late"));
 c.s.state=core::State{.instance=2};assert(app.on_start(c));assert(app.model_.state().remaining==total && app.model_.state().phase==brick::Phase::Ready);
 assert(app.on_timer(c,old,"old timer"));assert(c.s.activity==1); // old id rejected
 c.s.state->instance=3;assert(app.on_timer(c,app.timer_,"old instance"));assert(c.s.activity==1);
 assert(app.on_stop(c));assert(app.on_stop(c)); // repeated cleanup safe
}
''')


if __name__ == '__main__':
    unittest.main()
