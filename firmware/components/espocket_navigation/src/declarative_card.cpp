#include "espocket/declarative_card.hpp"
#include "boost/json.hpp"
#include <algorithm>
#include <set>

namespace espocket {
namespace {
bool fields(const boost::json::object &object, std::initializer_list<std::string_view> allowed)
{
    return std::ranges::all_of(object, [&](const auto &entry) {
        return std::ranges::find(allowed, std::string_view(entry.key())) != allowed.end();
    });
}
std::string text(const boost::json::object &object, std::string_view key)
{
    const auto *value = object.if_contains(key);
    return value && value->is_string() ? std::string(value->as_string()) : std::string{};
}
bool safe_path(std::string_view path)
{
    if (path.size() < 2 || path.front() != '/' || path.back() == '/') return false;
    size_t start = 1;
    while (start < path.size()) {
        const auto end = path.find('/', start);
        const auto part = path.substr(start, end == path.npos ? path.size() - start : end - start);
        if (part.empty() || part == "." || part == ".." || std::ranges::any_of(part, [](unsigned char c) { return !((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
            (c >= '0' && c <= '9') || c == '_' || c == '-'); })) return false;
        if (end == path.npos) break;
        start = end + 1;
    }
    return true;
}
// Declarative v1 can open its registered target, but cannot execute App JS actions.
bool allowed_actions(const boost::json::value &value)
{
    if (value.is_object()) {
        for (const auto &entry : value.as_object()) {
            if (entry.key() == "action" &&
                (!entry.value().is_string() || entry.value().as_string() != CARD_OPEN_APP_ACTION)) return false;
            if (!allowed_actions(entry.value())) return false;
        }
    } else if (value.is_array()) {
        for (const auto &item : value.as_array()) if (!allowed_actions(item)) return false;
    }
    return true;
}
class DeclarativeCardModel final : public CardModel {
public:
    DeclarativeCardModel(std::string app, DeclarativeCardView view, std::string resources, CardMetadataReader reader)
        : app_(std::move(app)), view_(std::move(view)), resources_(std::move(resources)), reader_(std::move(reader)) {}
    CardView view() const override {
        return {.json = view_.json, .resource_directory = resources_, .screen = view_.screen, .actions = {}};
    }
    bool on_refresh(CardUi &ui) noexcept override {
        const auto metadata = reader_ ? reader_() : std::nullopt;
        if (!metadata || metadata->app_id != app_) return false;
        for (const auto &binding : view_.bindings) {
            if (!ui.set_text(binding.path, binding.source == "app.name" ? metadata->name : metadata->version)) return false;
        }
        return true;
    }
private:
    std::string app_;
    DeclarativeCardView view_;
    std::string resources_;
    CardMetadataReader reader_;
};
}

std::expected<DeclarativeCards, std::string> decode_declarative_cards(
    std::string_view json, const PageDeclaration &declaration)
{
    if (json.size() > 65'536 || !validate_page_declaration(declaration)) return std::unexpected("invalid_card_declaration");
    boost::system::error_code error;
    const auto value = boost::json::parse(json, error);
    if (error || !value.is_object()) return std::unexpected("invalid_card_declaration");
    const auto &root = value.as_object();
    const auto *version = root.if_contains("version");
    if (!version || !version->is_int64() || version->as_int64() != 1) return std::unexpected("unsupported_version");
    if (!fields(root, {"version", "appId", "cards"})) return std::unexpected("invalid_card_declaration");
    DeclarativeCards result{text(root, "appId"), {}};
    if (result.app_id != declaration.app_id) return std::unexpected("identity_mismatch");
    const auto *cards = root.if_contains("cards");
    if (!cards || !cards->is_array() || cards->as_array().size() > 32) return std::unexpected("invalid_card_declaration");
    std::set<std::string> seen;
    for (const auto &card : cards->as_array()) {
        if (!card.is_object() || !fields(card.as_object(), {"cardId", "screen", "gui", "bindings"})) return std::unexpected("invalid_card_declaration");
        const auto &object = card.as_object();
        DeclarativeCardView view{text(object, "cardId"), {}, text(object, "screen"), {}};
        if (!seen.insert(view.card_id).second ||
            std::ranges::none_of(declaration.cards, [&](const auto &declared) { return declared.card_id == view.card_id; })) {
            return std::unexpected("card_identity_mismatch");
        }
        if (!safe_path(view.screen) || view.screen.find('/', 1) != view.screen.npos) return std::unexpected("invalid_card_screen");
        const auto *gui = object.if_contains("gui");
        if (!gui || !gui->is_object() || !fields(gui->as_object(), {"version", "assets"}) ||
            text(gui->as_object(), "version").empty() || !allowed_actions(*gui)) return std::unexpected("invalid_card_gui");
        const auto *assets = gui->as_object().if_contains("assets");
        if (!assets || !assets->is_array() || assets->as_array().size() != 1 || !assets->as_array()[0].is_object()) return std::unexpected("invalid_card_gui");
        const auto &screen = assets->as_array()[0].as_object();
        if (text(screen, "type") != "viewScreen" || "/" + text(screen, "id") != view.screen) return std::unexpected("invalid_card_screen");
        view.json = boost::json::serialize(*gui);
        if (const auto *bindings = object.if_contains("bindings")) {
            if (!bindings->is_array() || bindings->as_array().size() > 32) return std::unexpected("invalid_card_bindings");
            std::set<std::string> paths;
            for (const auto &binding : bindings->as_array()) {
                if (!binding.is_object() || !fields(binding.as_object(), {"path", "source"})) return std::unexpected("invalid_card_bindings");
                CardTextBinding parsed{text(binding.as_object(), "path"), text(binding.as_object(), "source")};
                if (!safe_path(parsed.path) || !parsed.path.starts_with(view.screen + "/") ||
                    !paths.insert(parsed.path).second || (parsed.source != "app.name" && parsed.source != "app.version")) return std::unexpected("invalid_card_bindings");
                view.bindings.push_back(std::move(parsed));
            }
        }
        result.views.push_back(std::move(view));
    }
    if (seen.size() != declaration.cards.size()) return std::unexpected("card_identity_mismatch");
    return result;
}

CardModelFactory make_declarative_card_factory(
    DeclarativeCards definition, std::string resources, CardMetadataReader reader)
{
    return [definition = std::move(definition), resources = std::move(resources), reader = std::move(reader)](std::string_view id) -> std::unique_ptr<CardModel> {
        const auto view = std::ranges::find_if(definition.views, [&](const auto &candidate) { return candidate.card_id == id; });
        if (view == definition.views.end() || !reader) return nullptr;
        return std::make_unique<DeclarativeCardModel>(definition.app_id, *view, resources, reader);
    };
}
} // namespace espocket
