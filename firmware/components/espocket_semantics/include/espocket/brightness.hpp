#pragma once
#include "espocket/semantic_contract.hpp"
#include <expected>
#include <functional>
#include <mutex>
#include <optional>

namespace espocket::semantic {
struct BrightnessContext { double percent; };
struct BrightnessChanged { std::string target_id; double previous; double observed; Caller caller; };
struct BrightnessResult {
    ResultStatus status;
    std::optional<BrightnessContext> observed;
    std::optional<BrightnessChanged> event;
    std::string detail;
};

// Owner-local adapter. Read/write bind to one selected Display output. Admission
// is trusted composition, never a flag supplied by the request. No cached state.
// Admission and backend callbacks must not reenter this adapter.
class Brightness {
public:
    using Read = std::function<std::expected<double, std::string>()>;
    using Write = std::function<std::expected<void, std::string>(double)>;
    using Admission = std::function<Permission(const Access&)>;
    Brightness(std::string target_id, Read read, Write write, Admission admission);
    const Registration& discovery() const { return registration_; }
    LifetimeScope::Handle handle() const { return lifetime_.handle(); }
    void invalidate();
    std::expected<BrightnessContext, std::string> read(const Caller& caller);
    BrightnessResult set(const Caller& caller, double percent,
                         std::function<bool()> cancelled = {});
private:
    bool allowed(const Caller& caller, Operation operation) const;
    std::expected<double, std::string> observe();
    std::string target_;
    Read read_;
    Write write_;
    Admission admission_;
    Registration registration_;
    LifetimeScope lifetime_;
    std::mutex mutex_;
};
} // namespace espocket::semantic
