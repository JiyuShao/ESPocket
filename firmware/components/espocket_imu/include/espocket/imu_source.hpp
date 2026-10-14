#pragma once

#include <cstdint>
#include <expected>
#include <memory>
#include <string>

namespace espocket::imu {

enum class Error {
    unavailable,
    not_started,
    paused,
    io,
    invalid_sample,
};

struct Sample {
    // Linear acceleration in milli-g and angular rate in degrees/second.
    // Axes are board coordinates: +X/+Y/+Z are fixed to the PCB, not the UI.
    float accel_x_mg = 0;
    float accel_y_mg = 0;
    float accel_z_mg = 0;
    float gyro_x_dps = 0;
    float gyro_y_dps = 0;
    float gyro_z_dps = 0;
    uint64_t timestamp_us = 0;
    uint64_t generation = 0;
    bool accel_valid = false;
    bool gyro_valid = false;
};

class Source {
public:
    Source() = default;
    virtual ~Source() = default;
    Source(const Source &) = delete;
    Source &operator=(const Source &) = delete;

    virtual std::expected<void, Error> start() = 0;
    virtual std::expected<void, Error> stop() = 0;
    virtual std::expected<void, Error> pause() = 0;
    virtual std::expected<void, Error> resume() = 0;
    virtual std::expected<Sample, Error> read() = 0;
};

class UnavailableSource final : public Source {
public:
    std::expected<void, Error> start() override;
    std::expected<void, Error> stop() override;
    std::expected<void, Error> pause() override;
    std::expected<void, Error> resume() override;
    std::expected<Sample, Error> read() override;
};

// Board setup owns the bus and sensor registration. Until a board declares an
// IMU device, the production factory is deliberately explicit and safe.
std::shared_ptr<Source> create_board_source();
const char *error_name(Error error);

} // namespace espocket::imu
