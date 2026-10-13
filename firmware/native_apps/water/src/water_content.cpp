#include "water_content.hpp"
#include "src/misc/cache/instance/lv_image_cache.h"
#include <algorithm>
namespace espocket {
std::expected<void, std::string> WaterContent::attach(lv_obj_t *root)
{
    field_ = lv_obj_create(root);
    if (!field_) return std::unexpected("Water field allocation failed");
    lv_obj_remove_style_all(field_);
    lv_obj_remove_flag(field_, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_remove_flag(field_, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_size(field_, water::canvas_size, water::canvas_size); lv_obj_center(field_);
    lv_obj_set_style_bg_color(field_, lv_color_black(), 0);
    lv_obj_set_style_bg_opa(field_, LV_OPA_COVER, 0);
    lv_obj_add_event_cb(field_, draw, LV_EVENT_DRAW_MAIN, this);
    hint_ = lv_label_create(field_);
    if (!hint_) return std::unexpected("Water label allocation failed");
    lv_label_set_text(hint_, "水池准备中");
    lv_obj_set_style_text_color(hint_, lv_color_hex(0xA0B0C8), 0);
    lv_obj_align(hint_, LV_ALIGN_CENTER, 0, -150);
    return {};
}
void WaterContent::paint(std::shared_ptr<const water::Frame> next)
{
    if (!field_ || !hint_ || !next) return;
    const int y0 = frame_ ? std::min(frame_->y0, next->y0) : 0;
    const int y1 = frame_ ? std::max(frame_->y1, next->y1) : water::canvas_size - 1;
    if (frame_) lv_image_cache_drop(&strip_);
    const bool first = !frame_;
    frame_ = std::move(next);
    strip_ = {};
    strip_.header.magic = LV_IMAGE_HEADER_MAGIC;
    strip_.header.cf = LV_COLOR_FORMAT_RGB565;
    strip_.header.w = water::canvas_size;
    strip_.header.h = frame_->y1 - frame_->y0 + 1;
    strip_.header.stride = water::canvas_size * sizeof(uint16_t);
    strip_.data = reinterpret_cast<const uint8_t *>(frame_->pixels.data() + frame_->y0 * water::canvas_size);
    strip_.data_size = strip_.header.h * strip_.header.stride;
    if (first) {
        lv_label_set_text(hint_, "拖动水面搅动\n倾斜暂不可用");
        lv_obj_align(hint_, LV_ALIGN_CENTER, 0, -150);
    }
    lv_area_t area; lv_obj_get_coords(field_, &area);
    area.y2 = area.y1 + y1; area.y1 += y0;
    lv_obj_invalidate_area(field_, &area);
}
void WaterContent::draw(lv_event_t *event)
{
    auto *self = static_cast<WaterContent *>(lv_event_get_user_data(event));
    if (!self->field_ || !self->frame_) return;
    lv_area_t area; lv_obj_get_coords(self->field_, &area);
    area.y2 = area.y1 + self->frame_->y1; area.y1 += self->frame_->y0;
    lv_draw_image_dsc_t descriptor; lv_draw_image_dsc_init(&descriptor);
    descriptor.src = &self->strip_;
    lv_draw_image(lv_event_get_layer(event), &descriptor, &area);
}
void WaterContent::show_failure()
{
    if (hint_) lv_label_set_text(hint_, "水池启动失败\n请退出后重试");
}
void WaterContent::detach() noexcept
{
    if (field_) lv_obj_remove_event_cb(field_, draw);
    if (frame_) lv_image_cache_drop(&strip_);
    frame_.reset(); strip_ = {}; field_ = hint_ = nullptr;
}
}
