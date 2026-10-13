#pragma once
#include "brookesia/gui_lvgl/native_content.hpp"
#include "espocket/pinball_model.hpp"
#include "lvgl.h"
#include <optional>
namespace espocket {
class PinballContent final : public esp_brookesia::gui::lvgl::NativeContent {
public:
    std::expected<void, std::string> attach(lv_obj_t *root) override;
    void detach() noexcept override;
    void paint(const pinball::Model &model);
private:
    std::array<lv_obj_t *, pinball::bumper_count> bumpers_{};
    std::array<lv_obj_t *, pinball::target_count> targets_{};
    std::array<lv_obj_t *, 2> flippers_{};
    // LVGL borrows each line's points until the next paint/detach.
    std::array<std::array<lv_point_precise_t, 2>, 2> points_{};
    lv_obj_t *ball_ = nullptr, *score_ = nullptr, *ready_ = nullptr;
    std::optional<pinball::State> painted_;
};
}
