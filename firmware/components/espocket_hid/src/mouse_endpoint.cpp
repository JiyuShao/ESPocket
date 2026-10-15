#include "espocket/mouse_endpoint.hpp"
#include <algorithm>

namespace espocket::hid {
namespace { int clamp(int value) { return std::clamp(value, -127, 127); } }

std::array<uint8_t, 4> encode_boot_mouse_report(const MouseReport &report)
{
    return {static_cast<uint8_t>(report.buttons & 0x07), static_cast<uint8_t>(clamp(report.dx)),
            static_cast<uint8_t>(clamp(report.dy)), static_cast<uint8_t>(clamp(report.wheel))};
}

const char *error_name(Error error)
{
    switch (error) {
    case Error::unavailable: return "unavailable";
    case Error::not_started: return "not_started";
    case Error::paused: return "paused";
    case Error::disconnected: return "disconnected";
    case Error::invalid_report: return "invalid_report";
    case Error::io: return "io";
    }
    return "unknown";
}

std::expected<void, Error> UnavailableEndpoint::start() { return std::unexpected(Error::unavailable); }
std::expected<void, Error> UnavailableEndpoint::stop() { return {}; }
std::expected<void, Error> UnavailableEndpoint::pause() { return {}; }
std::expected<void, Error> UnavailableEndpoint::resume() { return std::unexpected(Error::unavailable); }
std::expected<void, Error> UnavailableEndpoint::send(const MouseReport &) { return std::unexpected(Error::unavailable); }
std::shared_ptr<Endpoint> create_board_endpoint() { return std::make_shared<UnavailableEndpoint>(); }
} // namespace espocket::hid
