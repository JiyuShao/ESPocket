#include "espocket/page_declaration_codec.hpp"

#include <algorithm>
#include <set>
#include "boost/json.hpp"

namespace espocket {
namespace {
std::string text(const boost::json::object &object, std::string_view key)
{
    const auto *value = object.if_contains(key);
    return value && value->is_string() ? std::string(value->as_string()) : std::string{};
}
bool fields(const boost::json::object &object, std::initializer_list<std::string_view> allowed)
{
    return std::ranges::all_of(object, [&](const auto &entry) {
        return std::ranges::find(allowed, std::string_view(entry.key())) != allowed.end();
    });
}
}

std::expected<void, std::string> validate_runtime_pages(const RuntimePageDefinition &definition)
{
    const auto &declaration = definition.declaration;
    if (!validate_page_declaration(declaration) || definition.screen_flow.empty()) {
        return std::unexpected("invalid_declaration");
    }
    std::set<std::pair<std::string, std::string>> seen;
    for (const auto &transition : definition.transitions) {
        if (transition.action.empty() ||
            std::ranges::find(declaration.page_ids, transition.from) == declaration.page_ids.end() ||
            std::ranges::find(declaration.page_ids, transition.to) == declaration.page_ids.end() ||
            !seen.emplace(transition.from, transition.to).second) {
            return std::unexpected("invalid_declaration");
        }
    }
    return {};
}

std::expected<RuntimePageDefinition, std::string> decode_runtime_pages(std::string_view json)
{
    if (json.size() > 16'384) return std::unexpected("invalid_declaration");
    boost::system::error_code error;
    auto value = boost::json::parse(json, error);
    if (error || !value.is_object()) return std::unexpected("invalid_declaration");
    const auto &object = value.as_object();
    const auto *version = object.if_contains("version");
    if (!version || !version->is_int64() || version->as_int64() != 1) {
        return std::unexpected("unsupported_version");
    }
    if (!fields(object, {"version", "appId", "rootPageId", "pageIds", "cards",
                         "backPresentation", "usesStandardBackControl", "presentation"})) {
        return std::unexpected("invalid_declaration");
    }
    RuntimePageDefinition result;
    auto &declaration = result.declaration;
    declaration.app_id = text(object, "appId");
    declaration.root_page_id = text(object, "rootPageId");
    const auto *pages = object.if_contains("pageIds");
    if (!pages || !pages->is_array()) return std::unexpected("invalid_declaration");
    for (const auto &page : pages->as_array()) {
        if (!page.is_string()) return std::unexpected("invalid_declaration");
        declaration.page_ids.emplace_back(page.as_string());
    }
    if (const auto *cards = object.if_contains("cards")) {
        if (!cards->is_array()) return std::unexpected("invalid_declaration");
        for (const auto &card : cards->as_array()) {
            if (!card.is_object() || !fields(card.as_object(), {"cardId", "targetPageId"})) {
                return std::unexpected("invalid_declaration");
            }
            const auto *target = card.as_object().if_contains("targetPageId");
            if (target && !target->is_string()) return std::unexpected("invalid_declaration");
            declaration.cards.push_back({text(card.as_object(), "cardId"), text(card.as_object(), "targetPageId")});
        }
    }
    if (const auto *back = object.if_contains("backPresentation")) {
        if (!back->is_string()) return std::unexpected("invalid_declaration");
        if (back->as_string() == "appOwned") declaration.back_presentation = BackPresentation::AppOwned;
        else if (back->as_string() != "framework") return std::unexpected("invalid_declaration");
    }
    if (const auto *standard = object.if_contains("usesStandardBackControl")) {
        if (!standard->is_bool()) return std::unexpected("invalid_declaration");
        declaration.uses_standard_back_control = standard->as_bool();
    }
    if (!validate_page_declaration(declaration)) return std::unexpected("invalid_declaration");
    const auto *presentation = object.if_contains("presentation");
    if (!presentation || !presentation->is_object() ||
        !fields(presentation->as_object(), {"screenFlow", "transitions"})) {
        return std::unexpected("invalid_declaration");
    }
    const auto &adapter = presentation->as_object();
    result.screen_flow = text(adapter, "screenFlow");
    const auto *transitions = adapter.if_contains("transitions");
    if (result.screen_flow.empty() || !transitions || !transitions->is_array()) {
        return std::unexpected("invalid_declaration");
    }
    for (const auto &item : transitions->as_array()) {
        if (!item.is_object() || !fields(item.as_object(), {"from", "to", "action"})) {
            return std::unexpected("invalid_declaration");
        }
        PageTransition transition{text(item.as_object(), "from"), text(item.as_object(), "to"), text(item.as_object(), "action")};
        result.transitions.push_back(std::move(transition));
    }
    if (!validate_runtime_pages(result)) return std::unexpected("invalid_declaration");
    return result;
}

std::string_view navigation_error_name(NavigationError error)
{
    switch (error) {
    case NavigationError::InvalidDeclaration: return "invalid_declaration";
    case NavigationError::NotStarted: return "not_started";
    case NavigationError::UnknownPage: return "unknown_page";
    case NavigationError::AtRoot: return "at_root";
    case NavigationError::RootPage: return "root_page";
    case NavigationError::TargetUnavailable: return "target_unavailable";
    case NavigationError::PresentationFailed: return "presentation_failed";
    case NavigationError::BackPending: return "back_pending";
    case NavigationError::BackCancelled: return "back_cancelled";
    case NavigationError::BackTimeout: return "back_timeout";
    case NavigationError::StaleRequest: return "stale_request";
    case NavigationError::DeclarationInUse: return "declaration_in_use";
    case NavigationError::IdentityMismatch: return "identity_mismatch";
    }
    return "invalid_state";
}

std::string encode_page_snapshot(const PageSnapshot &snapshot)
{
    return boost::json::serialize(boost::json::object{
        {"appId", snapshot.app_id}, {"pageId", snapshot.page_id},
        {"canBack", snapshot.can_back}, {"backPending", snapshot.back_pending}});
}

} // namespace espocket
