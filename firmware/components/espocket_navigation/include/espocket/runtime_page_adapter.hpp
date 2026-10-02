#pragma once

#include <atomic>
#include "espocket/page_declaration_codec.hpp"

namespace espocket {

// JSON boundary for a Runtime binding. Invoke on the serialized App owner task.
// Uses the same Navigator as System Back, Home lifecycle and test snapshots.
class RuntimePageAdapter {
public:
    using FlowPresenter = std::function<bool(std::string_view flow, std::string_view action,
                                            std::string_view from, std::string_view to)>;
    static std::expected<std::shared_ptr<RuntimePageAdapter>, std::string> create(
        RuntimePageDefinition definition, FlowPresenter presenter);
    std::expected<void, NavigationError> start();
    void stop();
    std::shared_ptr<PageNavigator> navigator() const { return navigator_; }
    std::expected<std::string, std::string> dispatch(std::string_view request_json, uint64_t now_ms);

private:
    struct BackState {
        std::atomic<BackDecision> decision = BackDecision::Allow;
        std::atomic<uint64_t> token = 0;
    };
    explicit RuntimePageAdapter(std::shared_ptr<PageNavigator> navigator) : navigator_(std::move(navigator)) {}
    std::shared_ptr<PageNavigator> navigator_;
    std::shared_ptr<BackState> back_;
};

} // namespace espocket
