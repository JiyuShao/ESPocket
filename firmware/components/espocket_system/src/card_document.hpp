#pragma once
#include "espocket/card_model.hpp"
#include "espocket/card_session.hpp"
#include "brookesia/system_core/system/gui_access.hpp"

namespace espocket {
class CardDocument final : public CardContent, public CardUi {
public:
    using Sink = std::function<void(std::string)>;
    // A new sink is captured on each show, so old GUI callbacks cannot act on a resumed slot.
    using SinkFactory = std::function<Sink()>;
    static std::unique_ptr<CardDocument> create(esp_brookesia::system::core::SystemGuiAccess &gui,
        std::unique_ptr<CardModel> model, SinkFactory sink);
    ~CardDocument() override;
    bool show() noexcept override;
    bool refresh() noexcept override;
    void pause() noexcept override;
    bool action(std::string_view action) noexcept override;
    bool set_text(std::string_view path, std::string_view text) override;
private:
    CardDocument(esp_brookesia::system::core::SystemGuiAccess &gui,
        std::unique_ptr<CardModel> model, CardView view, esp_brookesia::gui::DocumentId document, SinkFactory sink);
    esp_brookesia::system::core::SystemGuiAccess &gui_;
    std::unique_ptr<CardModel> model_;
    CardView view_;
    esp_brookesia::gui::DocumentId document_;
    SinkFactory sink_;
    bool visible_ = false;
    std::vector<esp_brookesia::gui::ScopedConnection> connections_;
};
}
