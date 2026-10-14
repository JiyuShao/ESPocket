"""Production App header/methods with the real PageNavigator and boundary doubles."""
import re
import unittest
from test_orbit import ROOT, run


class OrbitAppTest(unittest.TestCase):
    def test_navigation_instances_failure_cleanup_pause_resume_and_late_timer(self):
        header=(ROOT/'include/espocket/solar_system_app.hpp').read_text()
        header=re.sub(r'^#.*\n','',header,flags=re.M)
        header=header.replace(' : public esp_brookesia::system::core::IApp','').replace(' override','').replace('private:','public:')
        source=(ROOT/'src/solar_system_app.cpp').read_text()
        source=re.sub(r'^#.*\n','',source,flags=re.M)
        run(r'''
#include <cassert>
#include <algorithm>
#include <expected>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include "espocket/orbit_input.hpp"
#include "espocket/page_navigator.hpp"
int64_t now=1000000;int64_t esp_timer_get_time(){return now;}
namespace espocket {
namespace orbit {class Worker {public:
 enum class Status {Stopped,Starting,Ready,Failed};Status current=Status::Ready;
 bool fail_start=false,fail_stop=false,fail_pause=false,fail_resume=false;
 int starts=0,stops=0,pauses=0,resumes=0,submits=0;Kind kind=Kind::Moon;
 std::shared_ptr<const Frame>image;Attitude last;
 std::expected<void,std::string>start(Kind k){kind=k;++starts;return fail_start?std::expected<void,std::string>{std::unexpected("start")}:std::expected<void,std::string>{};}
 std::expected<void,std::string>stop(){++stops;return fail_stop?std::expected<void,std::string>{std::unexpected("stop")}:std::expected<void,std::string>{};}
 std::expected<void,std::string>pause(){++pauses;return fail_pause?std::expected<void,std::string>{std::unexpected("pause")}:std::expected<void,std::string>{};}
 std::expected<void,std::string>resume(){++resumes;return fail_resume?std::expected<void,std::string>{std::unexpected("resume")}:std::expected<void,std::string>{};}
 void submit(Attitude pose){++submits;last=pose;}auto take_frame(){auto out=image;image.reset();return out;}auto status(){return current;}
};}
class OrbitContent {public:int menus=0,views=0,failures=0;void paint(std::shared_ptr<const orbit::Frame>){}void show_menu(){++menus;}void show_viewer(){++views;}void show_failure(){++failures;}};
}
namespace esp_brookesia::gui {using NativeContentToken=int;}
namespace esp_brookesia::system::core {
using TimerId=int;
enum class AppKind{Native};enum class GuiRootKind{JsonString};enum class GuiAppLayer{AppDefault};
struct AppManifest{std::string id,name,version;std::vector<std::pair<std::string,std::string>>localized_names;AppKind kind;bool visible;std::vector<std::string>supported_systems;};
struct AppGuiDescriptor{GuiRootKind root_kind;std::string root;std::vector<int>resources;struct Flow{std::string screen_flow;GuiAppLayer layer;};std::vector<Flow>screen_flows;};
struct State{uint64_t instance=1;bool paused=false;std::optional<uint64_t>activity_epoch=5;bool suspended()const{return paused;}};
struct System{std::optional<State>state=State{};int activity=0;auto execution_state(){return state;}void report_user_activity(uint64_t,uint64_t){++activity;}};
struct Frame{bool valid=true,cancelled=false;uint32_t sequence=1;std::vector<espocket::orbit::Point>points;};
struct Gui{
 bool fail_mount=false,fail_read=false,fail_invoke=false;int mounts=0,unmounts=0,invokes=0;Frame frame;std::shared_ptr<espocket::OrbitContent>content;
 std::expected<int,std::string>mount_native_content(std::string_view,std::shared_ptr<espocket::OrbitContent>c){++mounts;if(fail_mount)return std::unexpected("mount");content=c;return 1;}
 void unmount_native_content(int){++unmounts;content.reset();}
 std::expected<Frame,std::string>read_native_pointer_frame(int){if(fail_read)return std::unexpected("read");return frame;}
 template<class F>std::expected<void,std::string>invoke_native_content(int,F f){if(fail_invoke)return std::unexpected("invoke");f(*content);++invokes;return {};}
};
struct Timer{bool fail=false;int next=1,stops=0;std::expected<int,std::string>start_periodic(std::string_view,int){if(fail)return std::unexpected("timer");return next++;}void stop(int){++stops;}};
struct AppContext{System s;Gui g;Timer t;auto&system_service(){return s;}auto&gui(){return g;}auto&timer(){return t;}};
}
''' + header + source + r'''
namespace espocket {const char solar_system_gui_json_start[]="";}
int main(){using namespace espocket;namespace core=esp_brookesia::system::core;SolarSystemApp app;core::AppContext c;
 auto created=PageNavigator::create(app.get_page_declaration(),[&](auto from,auto to){return app.present_page(from,to);});assert(created);
 auto nav=std::make_shared<PageNavigator>(std::move(*created));app.set_navigator(nav);
 c.s.state.reset();assert(!app.on_start(c)&&c.g.mounts==0);c.s.state=core::State{};
 c.g.fail_mount=true;assert(!app.on_start(c)&&!app.content_);c.g.fail_mount=false;c.t.fail=true;assert(!app.on_start(c)&&c.g.unmounts==1);c.t.fail=false;
 assert(app.on_start(c));assert(nav->start());const int timer=app.timer_;assert(!nav->snapshot().can_back);
 auto tick=[&](std::vector<orbit::Point>points){c.g.frame.points=points;c.g.frame.sequence++;now+=33000;return app.on_timer(c,timer,"orbit.tick");};
 assert(tick({}));assert(tick({{233,200,1}}));assert(tick({}));assert(nav->snapshot().page_id=="globe"&&app.viewer_&&app.worker_->kind==orbit::Kind::Earth);
 assert(tick({{233,233,1}}));assert(c.s.activity==2); // Held selection is ignored until release.
 assert(tick({}));assert(tick({{233,233,2}}));assert(tick({{253,240,2}}));auto pose=app.motion_.attitude();const int submits=app.worker_->submits;
 c.s.state->paused=true;assert(tick({{280,200,2}})&&app.worker_->submits==submits);
 app.worker_->fail_pause=true;assert(!app.on_pause(c)&&!app.running_);app.worker_->fail_pause=false;assert(app.on_pause(c));
 app.worker_->fail_resume=true;assert(!app.on_resume(c)&&!app.running_);app.worker_->fail_resume=false;assert(app.on_resume(c));c.s.state->paused=false;
 now+=60000000;assert(tick({{280,200,2}}));assert(app.motion_.attitude().longitude==pose.longitude&&app.motion_.attitude().tilt==pose.tilt);
 c.g.fail_read=true;assert(!tick({}));c.g.fail_read=false;
 c.g.fail_invoke=true;assert(!nav->request_back(100));assert(nav->snapshot().page_id=="globe"&&app.viewer_);c.g.fail_invoke=false;
 assert(nav->request_back(100));assert(nav->snapshot().page_id=="root"&&!app.viewer_&&!nav->snapshot().can_back);
 assert(tick({}));assert(tick({{233,134,3}}));app.worker_->fail_start=true;assert(!tick({})&&!app.viewer_&&nav->snapshot().page_id=="root");
 app.worker_->fail_start=false;assert(tick({{233,134,3}}));assert(tick({}));assert(app.viewer_);
 app.motion_.cancel_touch();app.worker_->image=orbit::Frame::create();c.g.fail_invoke=true;
 const int before_retry=app.worker_->submits;assert(!tick({})&&app.worker_->submits==before_retry+2);c.g.fail_invoke=false;
 app.worker_->current=orbit::Worker::Status::Failed;c.g.fail_invoke=true;assert(!tick({})&&!app.failed_);c.g.fail_invoke=false;assert(tick({})&&app.failed_);
 const int invokes=c.g.invokes;assert(tick({})&&c.g.invokes==invokes);
 app.worker_->fail_stop=true;const int unmounts=c.g.unmounts;assert(!app.on_stop(c)&&app.content_&&c.g.unmounts==unmounts&&!app.context_);
 const int sent=app.worker_->submits;assert(tick({})&&app.worker_->submits==sent);assert(!app.present_page("globe","root"));
 app.worker_->fail_stop=false;assert(app.on_stop(c)&&!app.content_);nav->stop();c.s.state->instance=2;assert(app.on_start(c));assert(nav->start());
 assert(app.timer_!=timer);assert(app.on_timer(c,timer,"orbit.tick")&&app.worker_->submits==sent);
 c.s.state->instance=3;assert(app.on_timer(c,app.timer_,"orbit.tick")&&app.worker_->submits==sent);assert(!app.present_page("root","globe"));
 assert(app.on_stop(c));assert(app.on_stop(c));
}
''',sources=('orbit_renderer.cpp','orbit_textures.cpp','orbit_motion.cpp','../../../components/espocket_navigation/src/page_navigator.cpp'),flags=('-I',str(ROOT.parent.parent/'components/espocket_navigation/include')))

if __name__=='__main__':unittest.main()
