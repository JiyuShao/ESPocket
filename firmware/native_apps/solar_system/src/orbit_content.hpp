#pragma once
#include "brookesia/gui_lvgl/native_content.hpp"
#include "espocket/orbit_renderer.hpp"
#include "lvgl.h"
namespace espocket {
class OrbitContent final : public esp_brookesia::gui::lvgl::NativeContent {
public:
    std::expected<void, std::string> attach(lv_obj_t *) override;
    void detach() noexcept override;
    void show_menu();
    void show_viewer();
    void show_failure();
    void paint(std::shared_ptr<const orbit::Frame>);
private:
    static void draw(lv_event_t *);
    void drop_frame();
    lv_obj_t *field_ = nullptr, *title_ = nullptr;
    std::array<lv_obj_t *, 4> buttons_{};
    lv_image_dsc_t image_{};
    std::shared_ptr<const orbit::Frame> frame_;
};
}
