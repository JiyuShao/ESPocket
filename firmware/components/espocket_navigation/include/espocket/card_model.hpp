#pragma once
#include <functional>
#include <memory>
#include <string>
#include <string_view>
#include <vector>

namespace espocket {
struct CardView {
    std::string json;
    std::string resource_directory;
    std::string screen;
    std::vector<std::string> actions;
};

// App code can change only its own Card document. Calls belong to the App owner task.
class CardUi {
public:
    virtual ~CardUi() = default;
    virtual bool set_text(std::string_view path, std::string_view text) = 0;
};

class CardModel {
public:
    virtual ~CardModel() = default;
    virtual CardView view() const = 0;
    virtual bool on_show(CardUi &) noexcept { return true; }
    virtual bool on_refresh(CardUi &) noexcept = 0;
    virtual void on_pause() noexcept {}
    virtual bool on_action(CardUi &, std::string_view) noexcept { return false; }
};

using CardModelFactory = std::function<std::unique_ptr<CardModel>(std::string_view card_id)>;
inline constexpr std::string_view CARD_OPEN_APP_ACTION = "espocket.card.open";
}
