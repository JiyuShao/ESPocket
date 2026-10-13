#pragma once
#include "brookesia/gui_lvgl/native_content.hpp"
#include "espocket/brick_model.hpp"
#include "lvgl.h"
namespace espocket {
class BrickContent final : public esp_brookesia::gui::lvgl::NativeContent {
public:
    std::expected<void, std::string> attach(lv_obj_t *root) override;
    void detach() noexcept override;
    void paint(const brick::Model &model);
private:
    std::array<lv_obj_t *, brick::max_bricks> bricks_{};
    std::array<lv_obj_t *, 2> obstacles_{};
    lv_obj_t *paddle_ = nullptr, *ball_ = nullptr, *score_ = nullptr, *ready_ = nullptr;
    std::optional<brick::State> painted_;
};
}
