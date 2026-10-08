#pragma once

#include <expected>
#include <functional>
#include <string>
#include <string_view>

namespace espocket {

// A one-shot restart checkpoint. The persisted identifier is a request only:
// installation, opt-in and package trust are checked by the normal Core path.
class ResetResumeCheckpoint {
public:
    using Load = std::function<std::expected<std::string, std::string>()>;
    using Save = std::function<std::expected<void, std::string>(std::string_view)>;
    ResetResumeCheckpoint(Load load, Save save) : load_(std::move(load)), save_(std::move(save)) {}

    std::expected<void, std::string> remember(std::string_view id)
    {
        if (id == current_) return {};
        auto saved = save_(id);
        if (saved) current_ = id;
        return saved;
    }

    std::expected<std::string, std::string> consume(bool hardware_reset)
    {
        auto loaded = load_();
        if (!loaded) return std::unexpected(loaded.error());
        current_ = *loaded;
        auto saved = remember(""); // Clear before launch; failed launch cannot form a boot loop.
        if (!saved) return std::unexpected(saved.error());
        return hardware_reset ? *loaded : std::string{};
    }

private:
    Load load_;
    Save save_;
    std::string current_;
};

} // namespace espocket
