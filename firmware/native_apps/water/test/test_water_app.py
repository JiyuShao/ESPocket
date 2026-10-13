"""Execute production lifecycle methods with only Core/GUI/worker boundary doubles."""
import unittest
from test_water import ROOT, run


class WaterAppTest(unittest.TestCase):
    def test_failure_cleanup_pause_resume_stale_instances_and_stop_acknowledgement(self):
        source=(ROOT/'src/water_app.cpp').read_text()
        methods=source[source.index('std::expected<void, std::string> WaterApp::on_start('):]
        run(r'''
#include <cassert>
#include <expected>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include "espocket/water_input.hpp"
int64_t now=1000000;int64_t esp_timer_get_time(){return now;}
namespace espocket {
namespace water {
struct Worker {
 enum class Status {Starting,Ready,Failed};Status current=Status::Ready;
 bool fail_start=false,fail_stop=false,fail_pause=false,fail_resume=false;
 int starts=0,stops=0,pauses=0,resumes=0,submits=0,cancels=0;
 std::shared_ptr<const Frame>image;
 std::expected<void,std::string>start(){++starts;return fail_start?std::expected<void,std::string>{std::unexpected("start")}:std::expected<void,std::string>{};}
 std::expected<void,std::string>stop(){++stops;return fail_stop?std::expected<void,std::string>{std::unexpected("stop")}:std::expected<void,std::string>{};}
 std::expected<void,std::string>pause(){++pauses;return fail_pause?std::expected<void,std::string>{std::unexpected("pause")}:std::expected<void,std::string>{};}
 std::expected<void,std::string>resume(){++resumes;return fail_resume?std::expected<void,std::string>{std::unexpected("resume")}:std::expected<void,std::string>{};}
 void submit(uint64_t,Impulse){++submits;}void cancel_input(){++cancels;}
 auto take_frame(){auto out=image;image.reset();return out;}auto status(){return current;}
};
}
struct WaterContent {void paint(std::shared_ptr<const water::Frame>){}void show_failure(){}};
namespace core {
using TimerId=int;
struct State {uint64_t instance=1;bool paused=false;std::optional<uint64_t>activity_epoch=5;bool suspended()const{return paused;}};
struct System {std::optional<State>state=State{};int activity=0;auto execution_state(){return state;}void report_user_activity(uint64_t,uint64_t){++activity;}};
struct Frame {bool valid=true,cancelled=false;uint32_t sequence=1;std::vector<water::Point>points;};
struct Gui {
 bool fail_mount=false,fail_read=false,fail_paint=false;int mounts=0,unmounts=0,paints=0;Frame frame;
 std::expected<int,std::string>mount_native_content(std::string_view,std::shared_ptr<WaterContent>){++mounts;if(fail_mount)return std::unexpected("mount");return 1;}
 void unmount_native_content(int){++unmounts;}
 std::expected<Frame,std::string>read_native_pointer_frame(int){if(fail_read)return std::unexpected("read");return frame;}
 template<class F>std::expected<void,std::string>invoke_native_content(int,F f){if(fail_paint)return std::unexpected("paint");WaterContent c;f(c);++paints;return {};}
};
struct Timer {bool fail=false;int next=1,stops=0;std::expected<int,std::string>start_periodic(std::string_view,int){if(fail)return std::unexpected("timer");return next++;}void stop(int){++stops;}};
struct AppContext {System s;Gui g;Timer t;auto&system_service(){return s;}auto&gui(){return g;}auto&timer(){return t;}};
}
struct WaterApp {
 water::Input input_;std::unique_ptr<water::Worker>worker_=std::make_unique<water::Worker>();std::shared_ptr<WaterContent>content_;
 int mount_=0,timer_=0;uint64_t instance_=0;bool running_=false,has_frame_=false,failed_=false;uint32_t last_sequence_=0;
 std::expected<void,std::string>on_start(core::AppContext&);std::expected<void,std::string>on_pause(core::AppContext&);std::expected<void,std::string>on_resume(core::AppContext&);std::expected<void,std::string>on_stop(core::AppContext&);std::expected<void,std::string>on_timer(core::AppContext&,int,std::string_view);
};
''' + methods + r'''
int main(){using namespace espocket;WaterApp app;core::AppContext c;
 c.s.state.reset();assert(!app.on_start(c)&&c.g.mounts==0);
 c.s.state=core::State{};c.g.fail_mount=true;assert(!app.on_start(c)&&!app.content_);
 c.g.fail_mount=false;c.t.fail=true;assert(!app.on_start(c)&&c.g.unmounts==1&&app.worker_->starts==0);
 c.t.fail=false;app.worker_->fail_start=true;assert(!app.on_start(c)&&c.t.stops==1&&!app.content_);
 app.worker_->fail_start=false;assert(app.on_start(c));const int old=app.timer_;
 assert(app.on_timer(c,old,"release"));c.g.frame.sequence++;c.g.frame.points={{233,320,1}};assert(app.on_timer(c,old,"touch")&&c.s.activity==1);
 assert(app.on_timer(c,old,"duplicate")&&c.s.activity==1);
 c.g.fail_read=true;const int cancels=app.worker_->cancels;assert(!app.on_timer(c,old,"read error")&&app.worker_->cancels==cancels+1);c.g.fail_read=false;
 c.s.state->paused=true;const int before=app.worker_->submits;assert(app.on_timer(c,old,"covered")&&app.worker_->submits==before);
 app.worker_->fail_pause=true;assert(!app.on_pause(c)&&!app.running_);app.worker_->fail_pause=false;assert(app.on_pause(c));
 app.worker_->fail_resume=true;assert(!app.on_resume(c)&&!app.running_);app.worker_->fail_resume=false;assert(app.on_resume(c));c.s.state->paused=false;
 now+=60000000;assert(app.on_timer(c,old,"held after resume")&&c.s.activity==1);
 c.g.frame.sequence++;c.g.frame.points.clear();assert(app.on_timer(c,old,"release again"));
 c.g.frame.sequence++;c.g.frame.points={{233,320,2}};assert(app.on_timer(c,old,"new touch")&&c.s.activity==2);
 app.worker_->current=water::Worker::Status::Failed;c.g.fail_paint=true;assert(!app.on_timer(c,old,"failure paint retry")&&!app.failed_);
 c.g.fail_paint=false;assert(app.on_timer(c,old,"failure")&&app.failed_);const int paints=c.g.paints;assert(app.on_timer(c,old,"same failure")&&c.g.paints==paints);
 app.worker_->fail_stop=true;const int unmounts=c.g.unmounts;assert(!app.on_stop(c)&&app.content_&&c.g.unmounts==unmounts&&!app.running_);
 assert(app.on_timer(c,old,"late")&&app.worker_->submits==before+3);
 app.worker_->fail_stop=false;assert(app.on_stop(c)&&!app.content_&&c.g.unmounts==unmounts+1);
 app.worker_->current=water::Worker::Status::Ready;c.s.state=core::State{.instance=2};assert(app.on_start(c));assert(app.timer_!=old);
 const int submitted=app.worker_->submits;assert(app.on_timer(c,old,"old timer")&&app.worker_->submits==submitted);
 c.s.state->instance=3;assert(app.on_timer(c,app.timer_,"new instance")&&app.worker_->submits==submitted);
 assert(app.on_stop(c));assert(app.on_stop(c));
}
''')

if __name__=='__main__':unittest.main()
