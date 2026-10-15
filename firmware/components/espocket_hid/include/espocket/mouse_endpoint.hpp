#pragma once

#include <array>
#include <cstdint>
#include <expected>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace espocket::hid {

enum class Error { unavailable, not_started, paused, disconnected, invalid_report, io };

struct MouseReport {
    uint8_t buttons = 0;
    int dx = 0;
    int dy = 0;
    int wheel = 0;
};

std::array<uint8_t, 4> encode_boot_mouse_report(const MouseReport &report);
const char *error_name(Error error);

struct Peer {
    std::string address;
    std::string name;
};

class Endpoint {
public:
    virtual ~Endpoint() = default;
    Endpoint() = default;
    Endpoint(const Endpoint &) = delete;
    Endpoint &operator=(const Endpoint &) = delete;

    virtual std::expected<void, Error> start() = 0;
    virtual std::expected<void, Error> stop() = 0;
    virtual std::expected<void, Error> pause() = 0;
    virtual std::expected<void, Error> resume() = 0;
    virtual bool connected() const = 0;
    virtual std::optional<Peer> peer() const = 0;
    virtual std::expected<void, Error> send(const MouseReport &report) = 0;
    virtual void clear_buttons() = 0;
};

class UnavailableEndpoint final : public Endpoint {
public:
    std::expected<void, Error> start() override;
    std::expected<void, Error> stop() override;
    std::expected<void, Error> pause() override;
    std::expected<void, Error> resume() override;
    bool connected() const override { return false; }
    std::optional<Peer> peer() const override { return std::nullopt; }
    std::expected<void, Error> send(const MouseReport &) override;
    void clear_buttons() override {}
};

std::shared_ptr<Endpoint> create_board_endpoint();

} // namespace espocket::hid
