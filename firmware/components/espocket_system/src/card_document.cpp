#include "card_document.hpp"
#include <algorithm>
#include <set>

namespace espocket {
std::unique_ptr<CardDocument> CardDocument::create(
    esp_brookesia::system::core::SystemGuiAccess &gui, std::unique_ptr<CardModel> model, SinkFactory sink)
{
    if (!model || !sink) return nullptr;
    auto view = model->view();
    if (view.json.empty() || view.screen.empty()) return nullptr;
    std::set<std::string> seen;
    for (const auto &action : view.actions) {
        if (action.empty() || !seen.insert(action).second) return nullptr;
    }
    auto document = gui.load_json("espocket-card.json", view.json, view.resource_directory);
    if (!document) return nullptr;
    if (std::ranges::find(view.actions, CARD_OPEN_APP_ACTION) == view.actions.end()) {
        view.actions.emplace_back(CARD_OPEN_APP_ACTION);
    }
    return std::unique_ptr<CardDocument>(new CardDocument(gui, std::move(model), std::move(view), *document, std::move(sink)));
}

CardDocument::CardDocument(esp_brookesia::system::core::SystemGuiAccess &gui,
    std::unique_ptr<CardModel> model, CardView view, esp_brookesia::gui::DocumentId document, SinkFactory sink)
    : gui_(gui), model_(std::move(model)), view_(std::move(view)), document_(document), sink_(std::move(sink)) {}

CardDocument::~CardDocument()
{
    pause();
    gui_.unload(document_);
}

bool CardDocument::show() noexcept
{
    if (visible_) return true;
    const auto mounted = gui_.mount_screen(document_, view_.screen,
        {.display_id = {}, .layer = esp_brookesia::gui::GuiLayer::Default,
         .mount_mode = esp_brookesia::gui::MountStackMode::Stack, .z_order = 0});
    if (!mounted) return false;
    visible_ = true;
    const auto sink = sink_();
    if (!sink) return false;
    for (const auto &action : view_.actions) {
        auto connection = gui_.subscribe_action(document_, action,
            [sink, action](const auto &) { sink(action); });
        if (!connection.connected()) return false;
        connections_.push_back(std::move(connection));
    }
    return model_->on_show(*this);
}

bool CardDocument::refresh() noexcept { return visible_ && model_->on_refresh(*this); }
bool CardDocument::action(std::string_view action) noexcept { return visible_ && model_->on_action(*this, action); }
bool CardDocument::set_text(std::string_view path, std::string_view text)
{
    return visible_ && gui_.set_text(document_, path, text).has_value();
}

void CardDocument::pause() noexcept
{
    if (!visible_) return;
    connections_.clear();
    model_->on_pause();
    gui_.unmount_screen(document_, view_.screen);
    visible_ = false;
}
}
