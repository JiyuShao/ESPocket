#pragma once

#include <expected>
#include <optional>
#include "espocket/card_model.hpp"
#include "espocket/page_navigator.hpp"

namespace espocket {
struct CardMetadata {
    std::string app_id;
    std::string name;
    std::string version;
};
struct CardTextBinding {
    std::string path;
    std::string source;
};
struct DeclarativeCardView {
    std::string card_id;
    std::string json;
    std::string screen;
    std::vector<CardTextBinding> bindings;
};
struct DeclarativeCards {
    std::string app_id;
    std::vector<DeclarativeCardView> views;
};

// Installed declaration and Card presentation must have exactly the same stable IDs.
std::expected<DeclarativeCards, std::string> decode_declarative_cards(
    std::string_view json, const PageDeclaration &declaration);
using CardMetadataReader = std::function<std::optional<CardMetadata>()>;
// Reader is scoped to the real Core installation; never starts another Runtime.
CardModelFactory make_declarative_card_factory(
    DeclarativeCards definition, std::string resource_directory, CardMetadataReader reader);
} // namespace espocket
