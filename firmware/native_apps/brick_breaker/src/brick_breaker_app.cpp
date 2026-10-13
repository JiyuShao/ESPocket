#include "espocket/brick_breaker_app.hpp"
#include "brick_content.hpp"
#include "espocket/short_effect.hpp"
#include "esp_timer.h"
#include <algorithm>
namespace espocket {
namespace core = esp_brookesia::system::core;
extern const char brick_breaker_gui_json_start[] asm("_binary_brick_breaker_gui_json_start");
BrickBreakerApp::BrickBreakerApp() : sound_(std::make_unique<ShortEffect>("espocket.app.brick_breaker.effect")) {}
BrickBreakerApp::~BrickBreakerApp() = default;
PageDeclaration BrickBreakerApp::get_page_declaration() const
{
    return {.app_id = "espocket.app.brick_breaker", .root_page_id = "root", .page_ids = {"root"}};
}
bool BrickBreakerApp::present_page(std::string_view from, std::string_view to) const
{
    return from.empty() && to == "root";
}
core::AppManifest BrickBreakerApp::get_manifest() const
{
    core::AppManifest manifest;
    manifest.id = "espocket.app.brick_breaker"; manifest.name = "打砖块";
    manifest.localized_names = {{"zh_CN", "打砖块"}, {"en", "Brick Breaker"}};
    manifest.version = "0.1.0"; manifest.kind = core::AppKind::Native;
    manifest.visible = true; manifest.supported_systems = {"espocket"};
    return manifest;
}
core::AppGuiDescriptor BrickBreakerApp::get_gui_descriptor() const
{
    return {.root_kind = core::GuiRootKind::JsonString, .root = std::string(brick_breaker_gui_json_start),
        .resources = {}, .screen_flows = {{.screen_flow = "main", .layer = core::GuiAppLayer::AppDefault}}};
}
std::expected<void, std::string> BrickBreakerApp::on_start(core::AppContext &context)
{
    model_.reset(); has_frame_ = false;
    auto execution = context.system_service().execution_state();
    if (!execution) return std::unexpected("Running instance unavailable");
    instance_ = execution->instance;
    content_ = std::make_shared<BrickContent>();
    auto mounted = context.gui().mount_native_content("/root/content", content_);
    if (!mounted) { content_.reset(); return std::unexpected(mounted.error()); }
    mount_ = *mounted;
    auto timer = context.timer().start_periodic("brick.tick", 20);
    if (!timer) { context.gui().unmount_native_content(mount_); content_.reset(); return std::unexpected(timer.error()); }
    timer_ = *timer; running_ = true; last_tick_us_ = esp_timer_get_time();
    return {};
}
std::expected<void, std::string> BrickBreakerApp::on_pause(core::AppContext &)
{
    running_ = false; model_.suspend(); has_frame_ = false; sound_->close(); return {};
}
std::expected<void, std::string> BrickBreakerApp::on_resume(core::AppContext &)
{
    model_.suspend(); has_frame_ = false; last_tick_us_ = esp_timer_get_time(); running_ = true; return {};
}
std::expected<void, std::string> BrickBreakerApp::on_stop(core::AppContext &context)
{
    running_ = false; instance_ = 0; model_.cancel_input(); sound_->close();
    if (timer_) context.timer().stop(timer_);
    timer_ = 0;
    context.gui().unmount_native_content(mount_); content_.reset();
    return {};
}
std::expected<void, std::string> BrickBreakerApp::on_timer(core::AppContext &context, core::TimerId id, std::string_view)
{
    const auto state = context.system_service().execution_state();
    if (!running_ || !content_ || id != timer_ || !state || state->instance != instance_ || state->suspended()) return {};
    auto frame = context.gui().read_native_pointer_frame(mount_);
    if (!frame) { model_.cancel_input(); return std::unexpected(frame.error()); }
    const auto now = esp_timer_get_time();
    const auto elapsed = static_cast<uint32_t>(std::max<int64_t>(0, (now - last_tick_us_) / 1000));
    last_tick_us_ = now;
    std::vector<brick::Point> points;
    for (const auto &point : frame->points) points.push_back({point.x, point.y, point.track_id});
    const auto tones = model_.advance(elapsed, frame->valid, frame->cancelled, frame->sequence, points);
    if (frame->valid && !frame->cancelled && !points.empty() && state->activity_epoch &&
        (!has_frame_ || frame->sequence != last_sequence_))
        context.system_service().report_user_activity(instance_, *state->activity_epoch);
    has_frame_ = frame->valid && !frame->cancelled; last_sequence_ = frame->sequence;
    auto painted = context.gui().invoke_native_content(mount_, [this](auto &content) {
        static_cast<BrickContent &>(content).paint(model_);
    });
    sound_->poll();
    if (!tones.empty()) sound_->play(tones.front().hz, tones.front().ms);
    return painted;
}
}
