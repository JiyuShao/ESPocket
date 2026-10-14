#include "espocket/solar_system_app.hpp"
#include "orbit_content.hpp"
#include "orbit_worker.hpp"
#include "esp_timer.h"
#include <algorithm>
namespace espocket {
namespace core = esp_brookesia::system::core;
extern const char solar_system_gui_json_start[] asm("_binary_solar_system_gui_json_start");
SolarSystemApp::SolarSystemApp() : worker_(std::make_unique<orbit::Worker>()) {}
SolarSystemApp::~SolarSystemApp() = default;
PageDeclaration SolarSystemApp::get_page_declaration() const
{
    return {.app_id = "espocket.app.solar_system", .root_page_id = "root", .page_ids = {"root", "globe"}};
}
void SolarSystemApp::set_navigator(std::weak_ptr<PageNavigator> navigator) { navigator_ = std::move(navigator); }
bool SolarSystemApp::present_page(std::string_view from, std::string_view to)
{
    if (!context_ || !content_ || !running_) return false;
    const auto state = context_->system_service().execution_state();
    if (!state || state->instance != instance_ || state->suspended()) return false;
    if (from.empty() && to == "root") return true;
    if (from == "root" && to == "globe" && !viewer_) {
        if (!worker_->start(selected_)) return false;
        auto shown = context_->gui().invoke_native_content(mount_, [](auto &content) {
            static_cast<OrbitContent &>(content).show_viewer();
        });
        if (!shown) { worker_->stop(); return false; }
        motion_.reset(); input_.cancel(); last_ms_ = 0; failed_ = false; viewer_ = true;
        worker_->submit(motion_.attitude());
        return true;
    }
    if (from == "globe" && to == "root" && viewer_) {
        // Quiesce before changing presentation. A failed stop retains the viewer and its owners.
        if (!worker_->pause()) return false;
        auto shown = context_->gui().invoke_native_content(mount_, [](auto &content) {
            static_cast<OrbitContent &>(content).show_menu();
        });
        if (!shown) { worker_->resume(); return false; }
        // Stopping is bounded and does not depend on GUI; retain owners if it fails.
        auto stopped = worker_->stop();
        if (!stopped) {
            context_->gui().invoke_native_content(mount_, [](auto &content) {
                static_cast<OrbitContent &>(content).show_viewer();
                static_cast<OrbitContent &>(content).show_failure();
            });
            return false;
        }
        viewer_ = false; input_.cancel(); motion_.cancel_touch(); last_ms_ = 0;
        return true;
    }
    return false;
}
core::AppManifest SolarSystemApp::get_manifest() const
{
    core::AppManifest manifest;
    manifest.id = "espocket.app.solar_system"; manifest.name = "太阳系";
    manifest.localized_names = {{"zh_CN", "太阳系"}, {"en", "Orbit"}};
    manifest.version = "0.1.0"; manifest.kind = core::AppKind::Native;
    manifest.visible = true; manifest.supported_systems = {"espocket"};
    return manifest;
}
core::AppGuiDescriptor SolarSystemApp::get_gui_descriptor() const
{
    return {.root_kind = core::GuiRootKind::JsonString, .root = std::string(solar_system_gui_json_start),
        .resources = {}, .screen_flows = {{.screen_flow = "main", .layer = core::GuiAppLayer::AppDefault}}};
}
std::expected<void, std::string> SolarSystemApp::on_start(core::AppContext &context)
{
    const auto state = context.system_service().execution_state();
    if (!state) return std::unexpected("Running instance unavailable");
    content_ = std::make_shared<OrbitContent>();
    auto mounted = context.gui().mount_native_content("/root/content", content_);
    if (!mounted) { content_.reset(); return std::unexpected(mounted.error()); }
    mount_ = *mounted;
    auto timer = context.timer().start_periodic("orbit.tick", 33);
    if (!timer) {
        context.gui().unmount_native_content(mount_); content_.reset();
        return std::unexpected(timer.error());
    }
    timer_ = *timer; context_ = &context; instance_ = state->instance;
    input_.cancel(); motion_.reset(); last_ms_ = 0;
    viewer_ = failed_ = false; running_ = true;
    return {};
}
std::expected<void, std::string> SolarSystemApp::on_pause(core::AppContext &)
{
    running_ = false; input_.cancel(); motion_.cancel_touch(); last_ms_ = 0;
    return worker_->pause();
}
std::expected<void, std::string> SolarSystemApp::on_resume(core::AppContext &)
{
    input_.cancel(); motion_.cancel_touch(); motion_.request_redraw(); last_ms_ = 0;
    auto resumed = worker_->resume();
    if (resumed) running_ = true;
    return resumed;
}
std::expected<void, std::string> SolarSystemApp::on_stop(core::AppContext &context)
{
    running_ = false; context_ = nullptr; instance_ = 0; input_.cancel();
    if (timer_) context.timer().stop(timer_);
    timer_ = 0;
    auto stopped = worker_->stop();
    if (!stopped) return stopped;
    context.gui().unmount_native_content(mount_); content_.reset(); viewer_ = false;
    return {};
}
std::expected<void, std::string> SolarSystemApp::on_timer(core::AppContext &context, core::TimerId id, std::string_view name)
{
    const auto state = context.system_service().execution_state();
    if (!running_ || !content_ || id != timer_ || name != "orbit.tick" || !state ||
        state->instance != instance_ || state->suspended()) return {};
    auto frame = context.gui().read_native_pointer_frame(mount_);
    if (!frame) { input_.cancel(); motion_.cancel_touch(); return std::unexpected(frame.error()); }
    std::vector<orbit::Point> points;
    for (const auto &point : frame->points) points.push_back({point.x, point.y, point.track_id});
    const auto input = input_.read(frame->valid, frame->cancelled, frame->sequence, points, viewer_);
    if (input.activity && state->activity_epoch)
        context.system_service().report_user_activity(instance_, *state->activity_epoch);
    if (input.selection && !viewer_) {
        auto navigator = navigator_.lock();
        if (!navigator) return std::unexpected("Orbit navigator unavailable");
        selected_ = *input.selection;
        if (!navigator->push("globe")) return std::unexpected("Orbit page presentation failed");
        return {};
    }
    if (!viewer_) return {};
    if (worker_->status() == orbit::Worker::Status::Failed) {
        if (failed_) return {};
        auto shown = context.gui().invoke_native_content(mount_, [](auto &content) {
            static_cast<OrbitContent &>(content).show_failure();
        });
        failed_ = shown.has_value(); return shown;
    }
    const auto now = static_cast<uint64_t>(esp_timer_get_time() / 1000);
    const unsigned elapsed = last_ms_ && now > last_ms_ ? static_cast<unsigned>(std::min<uint64_t>(200, now - last_ms_)) : 33;
    last_ms_ = now;
    if (motion_.advance(elapsed, input.touch)) worker_->submit(motion_.attitude());
    if (auto image = worker_->take_frame()) {
        auto painted = context.gui().invoke_native_content(mount_, [image = std::move(image)](auto &content) {
            static_cast<OrbitContent &>(content).paint(image);
        });
        // A failed GUI dispatch must not lose the last sharp image once motion is idle.
        if (!painted) worker_->submit(motion_.attitude());
        return painted;
    }
    return {};
}
}
