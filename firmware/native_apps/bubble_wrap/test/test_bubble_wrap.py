"""Exercise actual App/model code; GUI, timer and audio Owners are boundary doubles."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]


def run(code):
    with tempfile.TemporaryDirectory(prefix='bubble-wrap-test-') as d:
        cpp, binary = Path(d) / 'test.cpp', Path(d) / 'test'
        cpp.write_text(code)
        subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-I', str(ROOT / 'include'),
                        str(cpp), str(ROOT / 'src/bubble_model.cpp'), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=10)


class BubbleWrapTest(unittest.TestCase):
    def test_original_layout_pop_multitouch_refill_and_cancel(self):
        run(r'''
#include <cassert>
#include "espocket/bubble_model.hpp"
using namespace espocket::bubble;
int main(){
 Model model;const int total=model.remaining();assert(total==19);
 auto cells=model.cells();auto a=cells[0],b=cells[1];
 auto tones=model.advance(0,true,false,1,{{a.x,a.y,1},{b.x,b.y,2}});
 assert(tones.size()==2 && tones[0].hz>=760 && tones[0].hz<1380 && tones[0].ms==22);
 assert(model.remaining()==total-2);
 assert(model.advance(20,true,false,1,{{a.x,a.y,1}}).empty()); // repeated snapshot
 assert(model.remaining()==total-2);
 model.advance(20,false,true,2,{{cells[2].x,cells[2].y,3}});assert(model.remaining()==total-2);
 // Cancel cannot become a delayed background long press.
 model.advance(1000,true,false,3,{});assert(model.remaining()==total-2);
 model.advance(0,true,false,4,{{20,233,4}});
 assert(model.advance(550,true,false,5,{}).empty());assert(model.remaining()==total-2); // released hold never fires
 model.advance(0,true,false,4,{{20,233,4}});
 tones=model.advance(550,true,false,5,{{20,233,4}});assert(tones.size()==1 && tones[0].hz==520);
 assert(model.remaining()==total);
 model.advance(0,true,false,6,{});
 for(size_t i=0;i<cells.size();++i){model.advance(0,true,false,7+2*i,{{cells[i].x,cells[i].y,static_cast<uint32_t>(i+10)}});model.advance(0,true,false,8+2*i,{});}
 assert(model.remaining()==0);
 model.advance(839,true,false,100,{});assert(model.remaining()==0);
 model.cancel_input(); // Pause/resume discards touch but does not consume refill time.
 tones=model.advance(1,true,false,101,{});assert(model.remaining()==total && tones[0].ms==130);
 model.advance(0,true,false,102,{{a.x,a.y,99}});assert(model.remaining()==total-1);
 model.reset();assert(model.remaining()==total);
}
''')

    def test_actual_app_pause_stop_start_failure_and_late_timer(self):
        source = (ROOT / 'src/bubble_wrap_app.cpp').read_text()
        methods = source[source.index('std::expected<void, std::string> BubbleWrapApp::on_start('):]
        run(r'''
#include <algorithm>
#include <cassert>
#include <expected>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include "espocket/bubble_model.hpp"
int64_t now=1000000;int64_t esp_timer_get_time(){return now;}
namespace espocket {
struct BubbleContent{int paints=0;void paint(const bubble::Model&){++paints;}};
struct BubbleSound{int plays=0,closes=0;void close(){++closes;}void poll(){}void play(unsigned,unsigned){++plays;}};
namespace core {
using TimerId=int;
struct State{uint64_t instance=1;bool paused=false;std::optional<uint64_t>activity_epoch=5;bool suspended()const{return paused;}};
struct System{std::optional<State>state=State{};int activity=0;auto execution_state(){return state;}void report_user_activity(uint64_t,uint64_t){++activity;}};
struct Frame{bool valid=true,cancelled=false;uint32_t sequence=1;std::vector<bubble::Point>points;};
struct Gui{
 bool fail_mount=false;int mounts=0,unmounts=0;Frame frame;
 std::expected<int,std::string>mount_native_content(std::string_view,std::shared_ptr<BubbleContent>){++mounts;if(fail_mount)return std::unexpected("mount");return 1;}
 void unmount_native_content(int){++unmounts;}
 std::expected<Frame,std::string>read_native_pointer_frame(int){return frame;}
 template<class F>std::expected<void,std::string>invoke_native_content(int,F f){BubbleContent content;f(content);return {};}
};
struct Timer{bool fail=false;int next=1,stops=0;std::expected<int,std::string>start_periodic(std::string_view,int){if(fail)return std::unexpected("timer");return next++;}void stop(int){++stops;}};
struct AppContext{System s;Gui g;Timer t;auto&system_service(){return s;}auto&gui(){return g;}auto&timer(){return t;}};
}
struct BubbleWrapApp{
 bubble::Model model_;std::shared_ptr<BubbleContent>content_;std::unique_ptr<BubbleSound>sound_=std::make_unique<BubbleSound>();
 int mount_=0,timer_=0;uint64_t instance_=0;int64_t last_tick_us_=0;bool running_=false,has_frame_=false;uint32_t last_sequence_=0;
 std::expected<void,std::string>on_start(core::AppContext&);std::expected<void,std::string>on_pause(core::AppContext&);
 std::expected<void,std::string>on_resume(core::AppContext&);std::expected<void,std::string>on_stop(core::AppContext&);
 std::expected<void,std::string>on_timer(core::AppContext&,int,std::string_view);
};
''' + methods + r'''
int main(){
 using namespace espocket;core::AppContext c;BubbleWrapApp app;
 c.s.state.reset();assert(!app.on_start(c));assert(c.g.mounts==0);
 c.s.state=core::State{};c.g.fail_mount=true;assert(!app.on_start(c));assert(!app.content_);
 c.g.fail_mount=false;c.t.fail=true;assert(!app.on_start(c));assert(c.g.unmounts==1 && !app.content_);
 c.t.fail=false;assert(app.on_start(c));int old=app.timer_;const int total=app.model_.remaining();
 auto cell=app.model_.cells()[0];c.g.frame.points={{cell.x,cell.y,1}};
 now+=20000;assert(app.on_timer(c,old,"tick"));assert(app.model_.remaining()==total-1 && c.s.activity==1);
 assert(app.on_pause(c));now+=60000000;assert(app.on_timer(c,old,"late"));assert(c.s.activity==1);
 c.g.frame.cancelled=true;c.g.frame.points.clear();assert(app.on_resume(c));
 now+=20000;assert(app.on_timer(c,old,"tick"));assert(app.model_.remaining()==total-1);
 assert(app.on_stop(c));assert(!app.content_ && c.t.stops==1);assert(app.on_timer(c,old,"late"));
 c.s.state=core::State{.instance=2};assert(app.on_start(c));assert(app.model_.remaining()==total);
 assert(app.on_timer(c,old,"old timer"));assert(c.s.activity==1); // old id rejected
 c.s.state->instance=3;assert(app.on_timer(c,app.timer_,"old instance"));assert(c.s.activity==1);
 assert(app.on_stop(c));assert(app.on_stop(c)); // repeated cleanup safe
}
''')


if __name__ == '__main__':
    unittest.main()
