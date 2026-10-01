#include "espocket/test_protocol.hpp"

#include <utility>

namespace espocket {

TestProtocol::TestProtocol(DeveloperMode &mode, std::string image_identity, SnapshotReader snapshot_reader)
    : mode_(mode), image_identity_(std::move(image_identity)),
      snapshot_reader_(std::move(snapshot_reader))
{}

TestReply TestProtocol::dispatch(uint32_t version, std::string_view operation)
{
    std::unique_lock lock(dispatch_mutex_, std::try_to_lock);
    if (!lock.owns_lock()) {
        return {.ok = false, .error_code = "busy", .image_identity = {}, .capabilities = {}};
    }
    if (version != VERSION) {
        return {.ok = false, .error_code = "bad_request", .image_identity = {}, .capabilities = {}};
    }
    if (!mode_.enabled()) {
        return {.ok = false, .error_code = "developer_mode_off", .image_identity = {}, .capabilities = {}};
    }
    if (operation == "hello") {
        std::vector<std::string> capabilities = {"hello"};
        if (snapshot_reader_) {
            capabilities.emplace_back("snapshot");
        }
        return {
            .ok = true,
            .error_code = {},
            .image_identity = image_identity_,
            .capabilities = std::move(capabilities),
        };
    }
    if (operation == "snapshot" && snapshot_reader_) {
        auto snapshot = snapshot_reader_();
        if (!snapshot) {
            return {.ok = false, .error_code = "invalid_state", .image_identity = {}, .capabilities = {}};
        }
        snapshot->seq = ++snapshot_seq_;
        return {.ok = true, .error_code = {}, .image_identity = {}, .capabilities = {},
                .snapshot = std::move(*snapshot)};
    }
    return {.ok = false, .error_code = "unsupported", .image_identity = {}, .capabilities = {}};
}

} // namespace espocket
