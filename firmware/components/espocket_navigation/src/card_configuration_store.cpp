#include "espocket/card_configuration_store.hpp"
#include "boost/json.hpp"
#include <set>

namespace espocket {
std::expected<CardConfiguration, std::string> decode_card_configuration(std::string_view json)
{
    if (json.size() > 16'384) return std::unexpected("invalid_configuration");
    boost::system::error_code error;
    const auto value = boost::json::parse(json, error);
    if (error || !value.is_object()) return std::unexpected("invalid_configuration");
    const auto &object = value.as_object();
    const auto *version = object.if_contains("version");
    if (!version || !version->is_int64() || version->as_int64() != 1) return std::unexpected("unsupported_version");
    if (object.size() != 3) return std::unexpected("invalid_configuration");
    CardConfiguration result;
    std::set<std::pair<std::string, std::string>> seen;
    for (auto [name, side] : {std::pair{"left", &result.left}, std::pair{"right", &result.right}}) {
        const auto *entries = object.if_contains(name);
        if (!entries || !entries->is_array()) return std::unexpected("invalid_configuration");
        for (const auto &item : entries->as_array()) {
            if (!item.is_object() || item.as_object().size() != 2) return std::unexpected("invalid_configuration");
            const auto *app = item.as_object().if_contains("appId");
            const auto *card = item.as_object().if_contains("cardId");
            if (!app || !app->is_string() || app->as_string().empty() ||
                !card || !card->is_string() || card->as_string().empty()) return std::unexpected("invalid_configuration");
            CardKey key{std::string(app->as_string()), std::string(card->as_string())};
            if (!seen.emplace(key.app_id, key.card_id).second) return std::unexpected("duplicate_card");
            side->push_back(std::move(key));
        }
    }
    return result;
}

std::string encode_card_configuration(const CardConfiguration &configuration)
{
    boost::json::object value{{"version", 1}};
    for (auto [name, side] : {std::pair{"left", &configuration.left}, std::pair{"right", &configuration.right}}) {
        boost::json::array entries;
        for (const auto &key : *side) entries.emplace_back(boost::json::object{{"appId", key.app_id}, {"cardId", key.card_id}});
        value[name] = std::move(entries);
    }
    return boost::json::serialize(value);
}

CardConfigurationStore::CardConfigurationStore(CardRegistry &registry, Load load, Save save)
    : registry_(registry), load_(std::move(load)), save_(std::move(save)) {}

std::expected<void, std::string> CardConfigurationStore::restore()
{
    if (!load_) return std::unexpected("storage_unavailable");
    auto stored = load_();
    if (!stored) return std::unexpected(stored.error());
    if (!stored->has_value()) return {};
    auto configuration = decode_card_configuration(stored->value());
    if (!configuration) return std::unexpected(configuration.error());
    if (!registry_.validate_configuration(*configuration)) return std::unexpected("declaration_unavailable");
    if (!registry_.replace_configuration(std::move(*configuration))) return std::unexpected("configuration_changed");
    return {};
}

std::expected<void, std::string> CardConfigurationStore::apply(CardConfiguration configuration)
{
    if (!registry_.validate_configuration(configuration)) return std::unexpected("invalid_configuration");
    if (!save_) return std::unexpected("storage_unavailable");
    const auto json = encode_card_configuration(configuration);
    if (json.size() > 16'384) return std::unexpected("invalid_configuration");
    if (auto saved = save_(json); !saved) return saved;
    if (!registry_.replace_configuration(std::move(configuration))) return std::unexpected("configuration_changed");
    return {};
}

std::expected<void, std::string> CardConfigurationStore::save_current()
{
    if (!save_) return std::unexpected("storage_unavailable");
    const auto json = encode_card_configuration(registry_.configuration());
    if (json.size() > 16'384) return std::unexpected("invalid_configuration");
    return save_(json);
}
} // namespace espocket
