#pragma once

#include <string>
#include <string_view>

namespace espocket::detail {

inline constexpr std::string_view TEST_FRAME_PREFIX = "@ESPTEST ";

inline std::string encode_usb_response(std::string_view json)
{
    // Console writers may leave a partial line before this response.
    return "\n" + std::string(TEST_FRAME_PREFIX) + std::string(json) + "\n";
}

} // namespace espocket::detail
