#pragma once
#include "brookesia/gui_lvgl/native_content.hpp"
#include "espocket/water_simulation.hpp"
#include "lvgl.h"
namespace espocket {
class WaterContent final : public esp_brookesia::gui::lvgl::NativeContent {
public:
    std::expected<void, std::string> attach(lv_obj_t *root) override;
    void detach() noexcept override;
    void paint(std::shared_ptr<const water::Frame>);
    void show_failure();
private:
    static void draw(lv_event_t *);
    lv_obj_t *field_ = nullptr, *hint_ = nullptr;
    lv_image_dsc_t strip_{};
    std::shared_ptr<const water::Frame> frame_;
};
}
