#include "espocket/hello_app.hpp"

namespace espocket {
extern const char hello_card_json_start[] asm("_binary_hello_card_json_start");
namespace {
class HelloCard final : public CardModel {
public:
    HelloCard(std::string name, std::string version, bool detail)
        : name_(std::move(name)), version_(std::move(version)), detail_(detail) {}
    CardView view() const override {
        return {.json = std::string(hello_card_json_start), .resource_directory = {},
                .screen = "/card", .actions = {}};
    }
    bool on_refresh(CardUi &ui) noexcept override {
        return ui.set_text("/card/title", name_) &&
               ui.set_text("/card/version", "Version: " + version_) &&
               ui.set_text("/card/open/label", detail_ ? "Open Detail" : "Open App");
    }
private:
    std::string name_, version_;
    bool detail_;
};
}
CardModelFactory HelloApp::get_card_factory() const
{
    const auto manifest = get_manifest();
    return [name = manifest.name, version = manifest.version](std::string_view id) -> std::unique_ptr<CardModel> {
        if (id != "summary" && id != "detail") return nullptr;
        return std::make_unique<HelloCard>(name, version, id == "detail");
    };
}
}
