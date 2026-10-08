#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <utility>

namespace espocket {
enum class ShellSurface : uint8_t;

struct RunningInstanceIdentity {
    uint32_t app_id;
    uint64_t generation;
    friend bool operator==(const RunningInstanceIdentity &, const RunningInstanceIdentity &) = default;
};

// System Owner projection only. Every recovery consumes a fresh Core-derived
// identity; these targets neither assert App state nor restart an instance.
class ForegroundRestorationProjection {
public:
    struct DisplayTarget {
        uint32_t source_id;
        uint32_t gui_source_id;
        std::string source_name;
    };

    explicit ForegroundRestorationProjection(ShellSurface home) : home_(home) {}

    void launch_requested(uint32_t app_id, ShellSurface source) { launch_ = LaunchTarget{app_id, source}; }
    void home_requested(uint32_t app_id) {
        launch_requested(app_id, home_);
        display_.reset();
    }
    void instance_started(uint32_t app_id) {
        if (launch_ && launch_->app_id == app_id) launch_.reset();
    }
    ShellSurface lifecycle_return(uint32_t app_id) {
        if (!launch_ || launch_->app_id != app_id) return home_;
        return std::exchange(launch_, std::nullopt)->source;
    }
    void screen_off(std::optional<RunningInstanceIdentity> instance) { wake_ = instance; }
    std::optional<RunningInstanceIdentity> sleeping_instance() const { return wake_; }
    bool wake_requires_home(std::optional<RunningInstanceIdentity> current) {
        const auto saved = std::exchange(wake_, std::nullopt);
        return saved && saved != current;
    }
    void quick_settings_opened(DisplayTarget target, std::optional<RunningInstanceIdentity> instance) {
        display_ = DisplayReturn{std::move(target), instance};
    }
    std::optional<DisplayTarget> quick_settings_closed(std::optional<RunningInstanceIdentity> current, bool restore) {
        auto saved = std::exchange(display_, std::nullopt);
        if (!restore || !saved || saved->instance != current ||
                (!saved->instance && saved->target.source_id != saved->target.gui_source_id)) return std::nullopt;
        return std::move(saved->target);
    }
    void reset() { launch_.reset(); wake_.reset(); display_.reset(); }

private:
    struct LaunchTarget { uint32_t app_id; ShellSurface source; };
    struct DisplayReturn { DisplayTarget target; std::optional<RunningInstanceIdentity> instance; };
    ShellSurface home_;
    std::optional<LaunchTarget> launch_;
    std::optional<RunningInstanceIdentity> wake_;
    std::optional<DisplayReturn> display_;
};
} // namespace espocket
