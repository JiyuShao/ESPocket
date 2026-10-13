#include "espocket/water_app.hpp"
#include "water_content.hpp"
#include "water_worker.hpp"
#include "esp_timer.h"
#include <algorithm>
namespace espocket {
namespace core = esp_brookesia::system::core;
extern const char water_gui_json_start[] asm("_binary_water_gui_json_start");
WaterApp::WaterApp() : worker_(std::make_unique<water::Worker>()) {}
WaterApp::~WaterApp() = default;
PageDeclaration WaterApp::get_page_declaration() const
{
    return {.app_id = "espocket.app.water", .root_page_id = "root", .page_ids = {"root"}};
}
bool WaterApp::present_page(std::string_view from, std::string_view to) const
{
    return from.empty() && to == "root";
}
core::AppManifest WaterApp::get_manifest() const
{
    core::AppManifest manifest;
    manifest.id = "espocket.app.water"; manifest.name = "水池";
    manifest.localized_names = {{"zh_CN", "水池"}, {"en", "Water"}};
    manifest.version = "0.1.0"; manifest.kind = core::AppKind::Native;
    manifest.visible = true; manifest.supported_systems = {"espocket"};
    return manifest;
}
core::AppGuiDescriptor WaterApp::get_gui_descriptor() const
{
    return {.root_kind = core::GuiRootKind::JsonString, .root = std::string(water_gui_json_start),
        .resources = {}, .screen_flows = {{.screen_flow = "main", .layer = core::GuiAppLayer::AppDefault}}};
}
std::expected<void, std::string> WaterApp::on_start(core::AppContext &context)
{
    input_.cancel(); has_frame_ = failed_ = false;
    const auto execution = context.system_service().execution_state();
    if (!execution) return std::unexpected("Running instance unavailable");
    instance_ = execution->instance;
    content_ = std::make_shared<WaterContent>();
    auto mounted = context.gui().mount_native_content("/root/content", content_);
    if (!mounted) { content_.reset(); return std::unexpected(mounted.error()); }
    mount_ = *mounted;
    // Prepare timer before starting the worker so failures cannot orphan active work.
    auto timer = context.timer().start_periodic("water.tick", 33);
    if (!timer) {
        context.gui().unmount_native_content(mount_); content_.reset();
        return std::unexpected(timer.error());
    }
    timer_ = *timer;
    const auto started = worker_->start();
    if (!started) {
        context.timer().stop(timer_); timer_ = 0;
        context.gui().unmount_native_content(mount_); content_.reset();
        return started;
    }
    running_ = true;
    return {};
}
std::expected<void, std::string> WaterApp::on_pause(core::AppContext &)
{
    running_ = false; input_.cancel(); has_frame_ = false;
    return worker_->pause();
}
std::expected<void, std::string> WaterApp::on_resume(core::AppContext &)
{
    input_.cancel(); has_frame_ = false;
    auto resumed = worker_->resume();
    if (resumed) running_ = true;
    return resumed;
}
std::expected<void, std::string> WaterApp::on_stop(core::AppContext &context)
{
    running_ = false; instance_ = 0; input_.cancel();
    if (timer_) context.timer().stop(timer_);
    timer_ = 0;
    auto stopped = worker_->stop();
    if (!stopped) return stopped; // Keep all resource owners alive until work really stops.
    context.gui().unmount_native_content(mount_); content_.reset();
    return {};
}
std::expected<void, std::string> WaterApp::on_timer(core::AppContext &context, core::TimerId id, std::string_view)
{
    const auto state = context.system_service().execution_state();
    if (!running_ || !content_ || id != timer_ || !state || state->instance != instance_ || state->suspended()) return {};
    if (worker_->status() == water::Worker::Status::Failed) {
        if (failed_) return {};
        auto result = context.gui().invoke_native_content(mount_, [](auto &content) {
            static_cast<WaterContent &>(content).show_failure();
        });
        failed_ = result.has_value();
        return result;
    }
    auto frame = context.gui().read_native_pointer_frame(mount_);
    if (!frame) { input_.cancel(); worker_->cancel_input(); return std::unexpected(frame.error()); }
    std::vector<water::Point> points;
    for (const auto &point : frame->points) points.push_back({point.x, point.y, point.track_id});
    const auto touch = input_.read(frame->valid, frame->cancelled, frame->sequence, points);
    if (!frame->valid || frame->cancelled || input_.waiting_for_release()) worker_->cancel_input();
    if (touch.active && state->activity_epoch && (!has_frame_ || frame->sequence != last_sequence_))
        context.system_service().report_user_activity(instance_, *state->activity_epoch);
    has_frame_ = frame->valid && !frame->cancelled; last_sequence_ = frame->sequence;
    worker_->submit(static_cast<uint64_t>(esp_timer_get_time() / 1000), touch);
    if (auto image = worker_->take_frame()) {
        return context.gui().invoke_native_content(mount_, [image = std::move(image)](auto &content) {
            static_cast<WaterContent &>(content).paint(image);
        });
    }
    return {};
}
}
