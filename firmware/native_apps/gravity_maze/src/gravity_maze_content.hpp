#pragma once
#include <expected>
#include <string>
#include <memory>
#include "brookesia/gui_lvgl/native_content.hpp"
#include "lvgl.h"
#include "espocket/gravity_maze_model.hpp"

namespace espocket {
class GravityMazeContent final : public esp_brookesia::gui::lvgl::NativeContent {
public:
    std::expected<void, std::string> attach(lv_obj_t *root) override;
    void detach() noexcept override;
    void paint(const gravity_maze::Model &model);
private:
    lv_obj_t *board_ = nullptr, *ring_ = nullptr, *hole_ = nullptr, *marble_ = nullptr;
    lv_obj_t *score_ = nullptr, *hint_ = nullptr;
    bool imu_available_ = false;
};
}
