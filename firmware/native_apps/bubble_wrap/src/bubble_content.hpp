#pragma once
#include "brookesia/gui_lvgl/native_content.hpp"
#include "espocket/bubble_model.hpp"
#include "lvgl.h"
namespace espocket {
class BubbleContent final : public esp_brookesia::gui::lvgl::NativeContent {
public:
    std::expected<void, std::string> attach(lv_obj_t *root) override;
    void detach() noexcept override;
    void paint(const bubble::Model &model);
private:
    std::vector<lv_obj_t *> cells_;
    std::vector<bool> painted_;
    lv_obj_t *label_ = nullptr;
    int remaining_ = -1;
};
}
