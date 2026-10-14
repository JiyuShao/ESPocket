#include "espocket/gravity_maze_app.hpp"
#include "gravity_maze_content.hpp"
#include "esp_timer.h"
#include <algorithm>

namespace espocket {
namespace core = esp_brookesia::system::core;
extern const char gravity_maze_gui_json_start[] asm("_binary_gravity_maze_gui_json_start");

GravityMazeApp::GravityMazeApp(std::shared_ptr<imu::Source> source) : imu_(std::move(source)) {}
GravityMazeApp::~GravityMazeApp() = default;
PageDeclaration GravityMazeApp::get_page_declaration() const { return {.app_id = "espocket.app.gravity_maze", .root_page_id = "root", .page_ids = {"root"}}; }
bool GravityMazeApp::present_page(std::string_view from, std::string_view to) const { return from.empty() && to == "root"; }
core::AppManifest GravityMazeApp::get_manifest() const
{
    core::AppManifest m; m.id = "espocket.app.gravity_maze"; m.name = "重力迷宫";
    m.localized_names = {{"zh_CN", "重力迷宫"}, {"en", "Gravity Maze"}}; m.version = "0.1.0";
    m.kind = core::AppKind::Native; m.visible = true; m.supported_systems = {"espocket"}; return m;
}
core::AppGuiDescriptor GravityMazeApp::get_gui_descriptor() const
{
    return {.root_kind = core::GuiRootKind::JsonString, .root = std::string(gravity_maze_gui_json_start),
            .resources = {}, .screen_flows = {{.screen_flow = "main", .layer = core::GuiAppLayer::AppDefault}}};
}
std::expected<void, std::string> GravityMazeApp::on_start(core::AppContext &context)
{
    auto execution = context.system_service().execution_state(); if (!execution) return std::unexpected("Running instance unavailable");
    instance_ = execution->instance; model_.reset(); content_ = std::make_shared<GravityMazeContent>();
    auto mounted = context.gui().mount_native_content("/root/content", content_);
    if (!mounted) { content_.reset(); return std::unexpected(mounted.error()); }
    mount_ = *mounted;
    auto timer = context.timer().start_periodic("gravity_maze.tick", 25);
    if (!timer) { context.gui().unmount_native_content(mount_); content_.reset(); return std::unexpected(timer.error()); }
    timer_ = *timer; imu_started_ = false; last_sample_timestamp_us_ = 0;
    if (imu_) { auto started = imu_->start(); imu_started_ = started.has_value(); model_.set_imu_available(imu_started_); }
    running_ = true; last_tick_us_ = esp_timer_get_time(); return {};
}
std::expected<void, std::string> GravityMazeApp::on_pause(core::AppContext &)
{
    running_ = false; model_.cancel_input(); if (imu_started_ && imu_) { auto paused = imu_->pause(); if (!paused) return std::unexpected(imu::error_name(paused.error())); } return {};
}
std::expected<void, std::string> GravityMazeApp::on_resume(core::AppContext &)
{
    model_.cancel_input(); last_tick_us_ = esp_timer_get_time();
    if (imu_) {
        auto resumed = imu_started_ ? imu_->resume() : imu_->start();
        imu_started_ = resumed.has_value(); model_.set_imu_available(imu_started_);
    }
    running_ = true; return {};
}
std::expected<void, std::string> GravityMazeApp::on_stop(core::AppContext &context)
{
    running_ = false; instance_ = 0; model_.cancel_input(); if (timer_) context.timer().stop(timer_); timer_ = 0;
    if (imu_started_ && imu_) imu_->stop(); imu_started_ = false;
    context.gui().unmount_native_content(mount_); content_.reset(); return {};
}
std::expected<void, std::string> GravityMazeApp::on_timer(core::AppContext &context, core::TimerId id, std::string_view)
{
    auto state = context.system_service().execution_state();
    if (!running_ || !content_ || id != timer_ || !state || state->instance != instance_ || state->suspended()) return {};
    auto frame = context.gui().read_native_pointer_frame(mount_); if (!frame) { model_.cancel_input(); return std::unexpected(frame.error()); }
    const auto now = esp_timer_get_time(); const auto elapsed = static_cast<uint32_t>(std::clamp<int64_t>((now - last_tick_us_) / 1000, 0, 200)); last_tick_us_ = now;
    std::vector<gravity_maze::Point> points; for (const auto &p : frame->points) points.push_back({p.x, p.y, p.track_id});
    std::optional<imu::Sample> sample;
    if (imu_started_ && imu_) {
        auto read = imu_->read();
        if (read && read->accel_valid &&
            (read->timestamp_us == 0 || read->timestamp_us > last_sample_timestamp_us_)) {
            sample = *read; last_sample_timestamp_us_ = read->timestamp_us;
        } else if (!read) {
            imu_->stop(); imu_started_ = false; model_.set_imu_available(false);
        }
    }
    model_.advance(elapsed, frame->valid, frame->cancelled, frame->sequence, points, sample);
    if (frame->valid && !frame->cancelled && !points.empty() && state->activity_epoch) context.system_service().report_user_activity(instance_, *state->activity_epoch);
    return context.gui().invoke_native_content(mount_, [this](auto &content) { static_cast<GravityMazeContent &>(content).paint(model_); });
}
}
