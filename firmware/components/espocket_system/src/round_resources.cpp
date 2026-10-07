#include "round_resources.hpp"

extern const unsigned char chat_round_start[] asm("_binary_espocket_chat_round_json_start");
extern const unsigned char chat_round_end[] asm("_binary_espocket_chat_round_json_end");
extern const unsigned char calculator_round_start[] asm("_binary_espocket_calculator_round_json_start");
extern const unsigned char calculator_round_end[] asm("_binary_espocket_calculator_round_json_end");

namespace espocket {
std::string_view chat_round_document()
{
    return {reinterpret_cast<const char *>(chat_round_start),
            static_cast<size_t>(chat_round_end - chat_round_start - 1)};
}
std::string_view calculator_round_document()
{
    return {reinterpret_cast<const char *>(calculator_round_start),
            static_cast<size_t>(calculator_round_end - calculator_round_start - 1)};
}
}
