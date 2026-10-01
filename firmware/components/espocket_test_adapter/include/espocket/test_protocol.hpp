#pragma once

#include <cstdint>
#include <mutex>
#include <string>
#include <string_view>
#include <vector>

#include "espocket/developer_mode.hpp"

namespace espocket {

struct TestReply {
    bool ok = false;
    std::string error_code;
    std::string image_identity;
    std::vector<std::string> capabilities;
};

class TestProtocol {
public:
    static constexpr uint32_t VERSION = 1;

    TestProtocol(DeveloperMode &mode, std::string image_identity);
    TestReply dispatch(uint32_t version, std::string_view operation);

private:
    DeveloperMode &mode_;
    std::string image_identity_;
    std::mutex dispatch_mutex_;
};

} // namespace espocket
