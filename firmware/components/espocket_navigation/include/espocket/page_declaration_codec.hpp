#pragma once

#include "espocket/page_navigator.hpp"

namespace espocket {

struct PageTransition {
    std::string from;
    std::string to;
    std::string action;
};

struct RuntimePageDefinition {
    PageDeclaration declaration;
    std::string screen_flow;
    std::vector<PageTransition> transitions;
};

// UTF-8 JSON, schema version 1. Semantic validation is shared with Native installation.
std::expected<RuntimePageDefinition, std::string> decode_runtime_pages(std::string_view json);
std::expected<void, std::string> validate_runtime_pages(const RuntimePageDefinition &definition);
std::string_view navigation_error_name(NavigationError error);
std::string encode_page_snapshot(const PageSnapshot &snapshot);

} // namespace espocket
