#include "espocket/imu_source.hpp"

namespace espocket::imu {

std::expected<void, Error> UnavailableSource::start() { return std::unexpected(Error::unavailable); }
std::expected<void, Error> UnavailableSource::stop() { return {}; }
std::expected<void, Error> UnavailableSource::pause() { return {}; }
std::expected<void, Error> UnavailableSource::resume() { return std::unexpected(Error::unavailable); }
std::expected<Sample, Error> UnavailableSource::read() { return std::unexpected(Error::unavailable); }

std::shared_ptr<Source> create_board_source() { return std::make_shared<UnavailableSource>(); }

const char *error_name(Error error)
{
    switch (error) {
    case Error::unavailable: return "unavailable";
    case Error::not_started: return "not_started";
    case Error::paused: return "paused";
    case Error::io: return "io";
    case Error::invalid_sample: return "invalid_sample";
    }
    return "unknown";
}

} // namespace espocket::imu
