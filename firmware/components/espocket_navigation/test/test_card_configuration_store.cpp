#include "espocket/card_configuration_store.hpp"
#include <cassert>

using namespace espocket;
int main()
{
    CardRegistry registry;
    assert(registry.register_app(PageDeclaration{"app", "root", {"root", "detail"}, {{"summary", "detail"}}}));
    std::optional<std::string> disk;
    bool storage_fail = false;
    int writes = 0;
    CardConfigurationStore store(registry, [&]() -> std::expected<std::optional<std::string>, std::string> { return disk; },
        [&](std::string_view json) -> std::expected<void, std::string> {
            if (storage_fail) return std::unexpected("write_failed");
            disk = std::string(json); ++writes; return {};
        });
    assert(store.restore() && writes == 0);
    CardConfiguration configuration{{{"app", "summary"}}, {}};
    assert(store.apply(configuration) && writes == 1);
    assert(decode_card_configuration(*disk)->left == configuration.left);
    assert(!store.apply({{{"app", "missing"}}, {}}) && writes == 1);
    assert(!store.apply({configuration.left, configuration.left}) && writes == 1);
    storage_fail = true;
    assert(store.apply({{}, configuration.left}).error() == "write_failed");
    assert(registry.configuration() == configuration && writes == 1);
    disk = "{}";
    assert(!store.restore() && registry.configuration() == configuration && writes == 1);
    disk = encode_card_configuration({{{"unknown", "summary"}}, {}});
    assert(store.restore().error() == "declaration_unavailable" && writes == 1);
    disk = encode_card_configuration({configuration.left, configuration.left});
    assert(decode_card_configuration(*disk).error() == "duplicate_card");
    assert(store.save_current().error() == "write_failed");
}
