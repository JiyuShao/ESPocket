#pragma once
#include <expected>
#include <string>
#include <string_view>
namespace espocket {
std::expected<void, std::string> initialize_runtime_render_probe();
void shutdown_runtime_render_probe();
void begin_runtime_render_probe(std::string_view manifest);
void end_runtime_render_probe();
}
