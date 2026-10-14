#include "orbit_content.hpp"
#include "espocket/orbit_input.hpp"
#include "src/misc/cache/instance/lv_image_cache.h"
namespace espocket {
std::expected<void, std::string> OrbitContent::attach(lv_obj_t *root)
{
    field_ = lv_obj_create(root);
    if (!field_) return std::unexpected("Orbit field allocation failed");
    lv_obj_remove_style_all(field_);
    lv_obj_remove_flag(field_, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_remove_flag(field_, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_size(field_, orbit::canvas_size, orbit::canvas_size); lv_obj_center(field_);
    lv_obj_set_style_bg_color(field_, lv_color_black(), 0);
    lv_obj_set_style_bg_opa(field_, LV_OPA_COVER, 0);
    lv_obj_add_event_cb(field_, draw, LV_EVENT_DRAW_MAIN, this);
    title_ = lv_label_create(field_);
    if (!title_) return std::unexpected("Orbit title allocation failed");
    lv_label_set_text(title_, "太阳系");
    lv_obj_set_style_text_color(title_, lv_color_hex(0x8A8A90), 0);
    lv_obj_align(title_, LV_ALIGN_CENTER, 0, -172);
    constexpr std::array<uint32_t, 4> colors{0x4A4A52, 0x2A5A7E, 0x8A5A18, 0x7A5A3A};
    constexpr std::array<const char *, 4> names{"月球", "地球", "太阳", "木星"};
    for (size_t i = 0; i < buttons_.size(); ++i) {
        buttons_[i] = lv_obj_create(field_);
        if (!buttons_[i]) return std::unexpected("Orbit menu allocation failed");
        lv_obj_remove_style_all(buttons_[i]);
        // Input is exclusively the System-arbitrated pointer frame; no raw LVGL click callbacks.
        lv_obj_remove_flag(buttons_[i], LV_OBJ_FLAG_CLICKABLE);
        lv_obj_remove_flag(buttons_[i], LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_set_size(buttons_[i], 250, 58);
        lv_obj_set_style_radius(buttons_[i], 29, 0);
        lv_obj_set_style_bg_color(buttons_[i], lv_color_hex(colors[i]), 0);
        lv_obj_set_style_bg_opa(buttons_[i], LV_OPA_COVER, 0);
        lv_obj_align(buttons_[i], LV_ALIGN_CENTER, 0, orbit::menu_centers[i] - orbit::center);
        auto *label = lv_label_create(buttons_[i]);
        if (!label) return std::unexpected("Orbit menu label allocation failed");
        lv_label_set_text(label, names[i]);
        lv_obj_set_style_text_color(label, lv_color_hex(0xFFFFFF), 0);
        lv_obj_center(label);
    }
    return {};
}
void OrbitContent::drop_frame()
{
    if (frame_) lv_image_cache_drop(&image_);
    frame_.reset(); image_ = {};
}
void OrbitContent::show_menu()
{
    drop_frame();
    if (!field_ || !title_) return;
    lv_label_set_text(title_, "太阳系");
    lv_obj_remove_flag(title_, LV_OBJ_FLAG_HIDDEN);
    lv_obj_align(title_, LV_ALIGN_CENTER, 0, -172);
    for (auto *button : buttons_) if (button) lv_obj_remove_flag(button, LV_OBJ_FLAG_HIDDEN);
    lv_obj_invalidate(field_);
}
void OrbitContent::show_viewer()
{
    drop_frame();
    if (!field_ || !title_) return;
    for (auto *button : buttons_) if (button) lv_obj_add_flag(button, LV_OBJ_FLAG_HIDDEN);
    lv_label_set_text(title_, "球体准备中");
    lv_obj_remove_flag(title_, LV_OBJ_FLAG_HIDDEN); lv_obj_center(title_);
    lv_obj_invalidate(field_);
}
void OrbitContent::show_failure()
{
    if (!title_) return;
    lv_label_set_text(title_, "球体启动失败\n请返回后重试");
    lv_obj_remove_flag(title_, LV_OBJ_FLAG_HIDDEN); lv_obj_center(title_);
}
void OrbitContent::paint(std::shared_ptr<const orbit::Frame> next)
{
    if (!field_ || !title_ || !next) return;
    drop_frame(); frame_ = std::move(next);
    image_.header.magic = LV_IMAGE_HEADER_MAGIC;
    image_.header.cf = LV_COLOR_FORMAT_RGB565;
    image_.header.w = image_.header.h = orbit::canvas_size;
    image_.header.stride = orbit::canvas_size * sizeof(uint16_t);
    image_.data = reinterpret_cast<const uint8_t *>(frame_->pixels.data());
    image_.data_size = image_.header.h * image_.header.stride;
    lv_obj_add_flag(title_, LV_OBJ_FLAG_HIDDEN);
    lv_obj_invalidate(field_);
}
void OrbitContent::draw(lv_event_t *event)
{
    auto *self = static_cast<OrbitContent *>(lv_event_get_user_data(event));
    if (!self->field_ || !self->frame_) return;
    lv_area_t area; lv_obj_get_coords(self->field_, &area);
    lv_draw_image_dsc_t descriptor; lv_draw_image_dsc_init(&descriptor);
    descriptor.src = &self->image_;
    lv_draw_image(lv_event_get_layer(event), &descriptor, &area);
}
void OrbitContent::detach() noexcept
{
    if (field_) lv_obj_remove_event_cb(field_, draw);
    drop_frame(); field_ = title_ = nullptr; buttons_ = {};
}
}
