#include "espocket/developer_mode.hpp"

#include <utility>

namespace espocket {

DeveloperMode::DeveloperMode(Load load, Save save)
    : load_(std::move(load)), save_(std::move(save))
{}

std::expected<void, std::string> DeveloperMode::restore()
{
    if (!load_) {
        return std::unexpected("Developer mode storage is unavailable");
    }
    auto value = load_();
    if (!value) {
        enabled_.store(false, std::memory_order_release);
        return std::unexpected(value.error());
    }
    enabled_.store(*value, std::memory_order_release);
    return {};
}

std::expected<void, std::string> DeveloperMode::set_enabled(bool enabled)
{
    if (!save_) {
        return std::unexpected("Developer mode storage is unavailable");
    }
    auto result = save_(enabled);
    if (!result) {
        return result;
    }
    enabled_.store(enabled, std::memory_order_release);
    return {};
}

bool DeveloperMode::enabled() const
{
    return enabled_.load(std::memory_order_acquire);
}

} // namespace espocket
