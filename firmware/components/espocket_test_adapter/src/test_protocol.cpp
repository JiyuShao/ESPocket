#include "espocket/test_protocol.hpp"

#include <utility>

namespace espocket {

TestProtocol::TestProtocol(DeveloperMode &mode, std::string image_identity)
    : mode_(mode), image_identity_(std::move(image_identity))
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
        return {
            .ok = true,
            .error_code = {},
            .image_identity = image_identity_,
            .capabilities = {"hello"},
        };
    }
    return {.ok = false, .error_code = "unsupported", .image_identity = {}, .capabilities = {}};
}

} // namespace espocket
