#include "espocket/declarative_card.hpp"
#include "espocket/card_session.hpp"
#include "boost/json.hpp"
#include <cassert>
#include <map>
#include <fstream>
#include <sstream>
#include "espocket/page_declaration_codec.hpp"

using namespace espocket;
struct Ui : CardUi {
    std::map<std::string, std::string> texts;
    bool fail = false;
    bool set_text(std::string_view path, std::string_view text) override {
        if (fail) return false;
        texts[std::string(path)] = text; return true;
    }
};
struct Content : CardContent {
    std::unique_ptr<CardModel> model;
    Ui &ui;
    int &pauses;
    Content(std::unique_ptr<CardModel> content, Ui &port, int &paused) : model(std::move(content)), ui(port), pauses(paused) {}
    bool show() noexcept override { return model->on_show(ui); }
    bool refresh() noexcept override { return model->on_refresh(ui); }
    void pause() noexcept override { ++pauses; model->on_pause(); }
};
int main(int argc, char **argv) {
    assert(argc == 3);
    auto read = [](const char *path) { std::ifstream file(path); assert(file); std::ostringstream content; content << file.rdbuf(); return content.str(); };
    const auto sample_pages = decode_runtime_pages(read(argv[1]));
    assert(sample_pages);
    const auto sample = decode_declarative_cards(read(argv[2]), sample_pages->declaration);
    assert(sample && sample->app_id == "espocket.app.hello_runtime" && sample->views.size() == 2);
    assert(sample_pages->declaration.cards[0].target_page_id == "root" && sample_pages->declaration.cards[1].target_page_id == "detail");
    PageDeclaration declaration{"app.runtime", "root", {"root", "detail"}, {{"summary", "root"}, {"detail", "detail"}}};
    const std::string json = R"({"version":1,"appId":"app.runtime","cards":[
       {"cardId":"summary","screen":"/card","gui":{"version":"0.1.0","assets":[{"type":"viewScreen","id":"card","children":[{"type":"label","id":"title"}]}]},"bindings":[{"path":"/card/title","source":"app.name"}]},
       {"cardId":"detail","screen":"/card","gui":{"version":"0.1.0","assets":[{"type":"viewScreen","id":"card","children":[{"type":"label","id":"version"}]}]},"bindings":[{"path":"/card/version","source":"app.version"}]}
    ]})";
    auto definition = decode_declarative_cards(json, declaration);
    assert(definition && definition->views.size() == 2);
    auto malformed = boost::json::parse(json);
    auto rejects = [&](std::string_view expected) {
        auto result = decode_declarative_cards(boost::json::serialize(malformed), declaration);
        assert(!result && result.error() == expected);
        malformed = boost::json::parse(json);
    };
    malformed.as_object()["version"] = 2; rejects("unsupported_version");
    malformed.as_object()["unknown"] = true; rejects("invalid_card_declaration");
    malformed.as_object()["appId"] = "other"; rejects("identity_mismatch");
    auto first = [&]() -> boost::json::object & { return malformed.at("cards").as_array()[0].as_object(); };
    first()["cardId"] = "unregistered"; rejects("card_identity_mismatch");
    first()["cardId"] = "detail"; rejects("card_identity_mismatch");
    malformed.at("cards").as_array().pop_back(); rejects("card_identity_mismatch");
    first()["screen"] = "/foreign"; rejects("invalid_card_screen");
    first()["screen"] = "/card/../other"; rejects("invalid_card_screen");
    first().at("gui").as_object()["include"] = "/foreign.json"; rejects("invalid_card_gui");
    first().at("gui").at("assets").as_array()[0].as_object()["events"] = boost::json::array{boost::json::object{{"action", "app.custom"}}};
    rejects("invalid_card_gui");
    first().at("bindings").as_array()[0].as_object()["path"] = "/other/title"; rejects("invalid_card_bindings");
    first().at("bindings").as_array()[0].as_object()["source"] = "form.password"; rejects("invalid_card_bindings");
    first().at("bindings").as_array()[0].as_object()["path"] = "/card/../title"; rejects("invalid_card_bindings");
    assert(!decode_declarative_cards(std::string(65'537, ' '), declaration));
    assert(!decode_declarative_cards("not-json", declaration));
    first().at("gui").at("assets").as_array()[0].as_object()["events"] = boost::json::array{boost::json::object{{"action", "espocket.card.open"}}};
    assert(decode_declarative_cards(boost::json::serialize(malformed), declaration));

    std::optional<CardMetadata> metadata = CardMetadata{"app.runtime", "Runtime", "1.0"};
    int reads = 0, pauses = 0;
    Ui ui;
    auto factory = make_declarative_card_factory(*definition, "/installed/res", [&] { ++reads; return metadata; });
    assert(!factory("unknown"));
    auto model = factory("summary");
    assert(model && model->view().screen == "/card" && model->view().resource_directory == "/installed/res");
    assert(model->view().actions.empty() && model->on_refresh(ui));
    assert(ui.texts["/card/title"] == "Runtime");
    metadata->name = "New name";
    assert(model->on_refresh(ui) && ui.texts["/card/title"] == "New name");
    metadata->app_id = "other";
    assert(!model->on_refresh(ui) && ui.texts["/card/title"] == "New name");
    metadata->app_id = "app.runtime";
    ui.fail = true; assert(!model->on_refresh(ui)); ui.fail = false;

    CardRegistry registry;
    assert(registry.register_app(declaration));
    const CardKey summary{"app.runtime", "summary"}, detail{"app.runtime", "detail"};
    assert(registry.add(summary, CardSide::Left, 0) && registry.add(detail, CardSide::Right, 0));
    CardSession session(registry, [&](const auto &key) { return std::make_unique<Content>(factory(key.card_id), ui, pauses); });
    auto navigator = PageNavigator::create(declaration, [](auto, auto) { return true; });
    assert(navigator);
    auto launch = [&](const CardKey &, std::string_view target) {
        assert(session.visibility() == CardVisibility::Paused);
        assert(navigator->start());
        return target == "root" || navigator->push(target).has_value();
    };
    assert(session.show(summary) && session.open_app(launch));
    assert(navigator->snapshot().page_id == "root" && !navigator->snapshot().can_back);
    navigator->stop();
    assert(session.show(detail) && session.open_app(launch));
    assert(navigator->snapshot().page_id == "detail" && navigator->snapshot().can_back);
    assert(navigator->pop() && navigator->snapshot().page_id == "root");
    navigator->stop(); assert(navigator->start() && navigator->snapshot().page_id == "root");
    const auto before_resume = reads;
    metadata->version = "2.0";
    assert(session.show(detail) && reads == before_resume + 1 && ui.texts["/card/version"] == "2.0");
    assert(session.pause()); const auto paused_reads = reads;
    assert(session.pause() && reads == paused_reads);
    metadata.reset();
    assert(session.show(detail).error() == CardSessionError::RefreshFailed);
    assert(session.visibility() == CardVisibility::Paused && pauses > 0);
    assert(registry.remove(detail));
    assert(session.show(detail).error() == CardSessionError::NotConfigured);
    assert(session.release());
}
