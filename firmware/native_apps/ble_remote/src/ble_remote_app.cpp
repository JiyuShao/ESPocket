#include "espocket/ble_remote_app.hpp"
#include "ble_remote_content.hpp"
#include "esp_timer.h"
#include <algorithm>

namespace espocket {
namespace core = esp_brookesia::system::core;
extern const char ble_remote_gui_json_start[] asm("_binary_ble_remote_gui_json_start");

BleRemoteApp::BleRemoteApp(std::shared_ptr<hid::Endpoint> endpoint, std::shared_ptr<imu::Source> imu_source)
    : endpoint_(std::move(endpoint)), imu_(std::move(imu_source)) {}
BleRemoteApp::~BleRemoteApp() = default;
PageDeclaration BleRemoteApp::get_page_declaration() const { return {.app_id = "espocket.app.ble_remote", .root_page_id = "root", .page_ids = {"root"}}; }
bool BleRemoteApp::present_page(std::string_view from, std::string_view to) const { return from.empty() && to == "root"; }
core::AppManifest BleRemoteApp::get_manifest() const
{
    core::AppManifest m; m.id = "espocket.app.ble_remote"; m.name = "蓝牙遥控";
    m.localized_names = {{"zh_CN", "蓝牙遥控"}, {"en", "BLE Remote"}}; m.version = "0.1.0";
    m.kind = core::AppKind::Native; m.visible = true; m.supported_systems = {"espocket"}; return m;
}
core::AppGuiDescriptor BleRemoteApp::get_gui_descriptor() const
{
    return {.root_kind = core::GuiRootKind::JsonString, .root = std::string(ble_remote_gui_json_start), .resources = {},
            .screen_flows = {{.screen_flow = "main", .layer = core::GuiAppLayer::AppDefault}}};
}
std::expected<void, std::string> BleRemoteApp::on_start(core::AppContext &context)
{
    auto execution = context.system_service().execution_state(); if (!execution) return std::unexpected("Running instance unavailable");
    instance_ = execution->instance; model_.reset(); content_ = std::make_shared<BleRemoteContent>();
    auto mounted = context.gui().mount_native_content("/root/content", content_); if (!mounted) { content_.reset(); return std::unexpected(mounted.error()); }
    mount_ = *mounted;
    auto timer = context.timer().start_periodic("ble_remote.tick", 15);
    if (!timer) { context.gui().unmount_native_content(mount_); content_.reset(); return std::unexpected(timer.error()); }
    timer_ = *timer; running_ = true; endpoint_started_ = false; imu_started_ = false; retry_ms_ = 0; last_sequence_ = 0; last_points_empty_ = true; last_tick_us_ = esp_timer_get_time();
    try_start();
    return {};
}
void BleRemoteApp::try_start()
{
    if (!endpoint_started_ && endpoint_) { auto started = endpoint_->start(); endpoint_started_ = started.has_value(); model_.set_connected(endpoint_started_ && endpoint_->connected()); }
    if (!imu_started_ && imu_) { auto started = imu_->start(); imu_started_ = started.has_value(); model_.set_imu_available(imu_started_); }
}
std::expected<void, std::string> BleRemoteApp::on_pause(core::AppContext &)
{
    running_ = false; model_.cancel_input(); if (endpoint_) endpoint_->clear_buttons();
    if (endpoint_started_ && endpoint_) endpoint_->pause(); if (imu_started_ && imu_) imu_->pause(); return {};
}
std::expected<void, std::string> BleRemoteApp::on_resume(core::AppContext &)
{
    model_.cancel_input(); last_tick_us_ = esp_timer_get_time();
    if (endpoint_) { auto resumed = endpoint_started_ ? endpoint_->resume() : endpoint_->start(); endpoint_started_ = resumed.has_value(); }
    if (imu_) { auto resumed = imu_started_ ? imu_->resume() : imu_->start(); imu_started_ = resumed.has_value(); model_.set_imu_available(imu_started_); }
    running_ = true; return {};
}
std::expected<void, std::string> BleRemoteApp::on_stop(core::AppContext &context)
{
    running_ = false; instance_ = 0; model_.cancel_input(); if (endpoint_) endpoint_->clear_buttons();
    if (timer_) context.timer().stop(timer_); timer_ = 0; if (endpoint_started_ && endpoint_) endpoint_->stop(); if (imu_started_ && imu_) imu_->stop();
    endpoint_started_ = imu_started_ = false; context.gui().unmount_native_content(mount_); content_.reset(); return {};
}
std::expected<void, std::string> BleRemoteApp::on_timer(core::AppContext &context, core::TimerId id, std::string_view)
{
    auto state = context.system_service().execution_state(); if (!running_ || !content_ || id != timer_ || !state || state->instance != instance_ || state->suspended()) return {};
    const auto now = esp_timer_get_time(); const auto elapsed = static_cast<uint32_t>(std::clamp<int64_t>((now - last_tick_us_) / 1000, 0, 200)); last_tick_us_ = now;
    retry_ms_ = std::min<uint32_t>(1000, retry_ms_ + elapsed); if (retry_ms_ >= 1000) { retry_ms_ = 0; try_start(); }
    auto frame = context.gui().read_native_pointer_frame(mount_); if (!frame) { model_.cancel_input(); if (endpoint_) endpoint_->clear_buttons(); return std::unexpected(frame.error()); }
    std::vector<hid::Point> points; for (const auto &p : frame->points) points.push_back({p.x, p.y, p.track_id});
    const bool fresh = frame->valid && !frame->cancelled && frame->sequence != last_sequence_;
    if (fresh && last_points_empty_ && !points.empty() && points.front().y < 85) model_.toggle_mode();
    std::optional<imu::Sample> sample; if (imu_started_ && imu_) { auto read = imu_->read(); if (read) sample = *read; else { imu_started_ = false; model_.set_imu_available(false); } }
    model_.set_connected(endpoint_started_ && endpoint_ && endpoint_->connected());
    auto reports = model_.advance(elapsed, frame->valid, frame->cancelled, frame->sequence, points, sample);
    for (const auto &report : reports) if (endpoint_started_ && endpoint_) endpoint_->send(report);
    if (fresh && !points.empty() && state->activity_epoch) context.system_service().report_user_activity(instance_, *state->activity_epoch);
    last_sequence_ = frame->sequence; last_points_empty_ = points.empty();
    return context.gui().invoke_native_content(mount_, [this](auto &content) { static_cast<BleRemoteContent &>(content).paint(model_, endpoint_started_, endpoint_ && endpoint_->connected()); });
}
}
