#pragma once
#include "brookesia/gui_lvgl/native_content.hpp"
#include "espocket/mouse_model.hpp"
#include "lvgl.h"
namespace espocket {
class BleRemoteContent final : public esp_brookesia::gui::lvgl::NativeContent {
public:
    std::expected<void, std::string> attach(lv_obj_t *root) override;
    void detach() noexcept override;
    void paint(const hid::MouseModel &model, bool endpoint_available, bool connected);
private:
    lv_obj_t *root_ = nullptr, *title_ = nullptr, *status_ = nullptr, *hint_ = nullptr;
};
}
