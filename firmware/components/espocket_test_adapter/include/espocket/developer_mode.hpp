#pragma once

#include <atomic>
#include <expected>
#include <functional>
#include <memory>
#include <string>

namespace espocket {

class DeveloperMode {
public:
    using Load = std::function<std::expected<bool, std::string>()>;
    using Save = std::function<std::expected<void, std::string>(bool)>;

    DeveloperMode(Load load, Save save);
    std::expected<void, std::string> restore();
    std::expected<void, std::string> set_enabled(bool enabled);
    bool enabled() const;

private:
    Load load_;
    Save save_;
    std::atomic_bool enabled_ = false;
};

std::shared_ptr<DeveloperMode> make_device_developer_mode();

} // namespace espocket
