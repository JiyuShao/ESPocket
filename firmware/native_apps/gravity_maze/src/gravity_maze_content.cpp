#include "gravity_maze_content.hpp"
#include <cmath>
namespace espocket {
std::expected<void, std::string> GravityMazeContent::attach(lv_obj_t *root)
{
    board_ = lv_obj_create(root); if (!board_) return std::unexpected("Board allocation failed");
    lv_obj_remove_style_all(board_); lv_obj_set_size(board_, 466, 466); lv_obj_center(board_);
    lv_obj_set_style_bg_color(board_, lv_color_hex(0x101014), 0); lv_obj_set_style_bg_opa(board_, LV_OPA_COVER, 0);
    ring_ = lv_arc_create(board_); if (!ring_) return std::unexpected("Ring allocation failed");
    lv_obj_remove_style_all(ring_); lv_obj_remove_flag(ring_, LV_OBJ_FLAG_CLICKABLE); lv_obj_set_size(ring_, 420, 420); lv_obj_center(ring_);
    lv_arc_set_bg_angles(ring_, 0, 360); lv_arc_set_value(ring_, 0); lv_obj_set_style_arc_width(ring_, 6, LV_PART_MAIN); lv_obj_set_style_arc_color(ring_, lv_color_hex(0x2A2A32), LV_PART_MAIN);
    hole_ = lv_obj_create(board_); marble_ = lv_obj_create(board_);
    if (!hole_ || !marble_) return std::unexpected("Marble allocation failed");
    for (auto *obj : {hole_, marble_}) { lv_obj_remove_style_all(obj); lv_obj_remove_flag(obj, LV_OBJ_FLAG_CLICKABLE); lv_obj_set_style_radius(obj, LV_RADIUS_CIRCLE, 0); }
    lv_obj_set_size(hole_, 34, 34); lv_obj_set_style_bg_color(hole_, lv_color_hex(0x3A3A44), 0);
    lv_obj_set_size(marble_, 22, 22); lv_obj_set_style_bg_color(marble_, lv_color_hex(0xE8E8F0), 0);
    score_ = lv_label_create(board_); hint_ = lv_label_create(board_); if (!score_ || !hint_) return std::unexpected("Label allocation failed");
    lv_obj_set_style_text_color(score_, lv_color_white(), 0); lv_obj_set_style_text_color(hint_, lv_color_hex(0xA8B0C0), 0);
    lv_label_set_text(score_, "0"); lv_label_set_text(hint_, "倾斜不可用 · 触摸控制");
    lv_obj_align(score_, LV_ALIGN_CENTER, 0, 168); lv_obj_align(hint_, LV_ALIGN_CENTER, 0, 196);
    paint(gravity_maze::Model{}); return {};
}
void GravityMazeContent::paint(const gravity_maze::Model &model)
{
    const auto &s = model.state();
    lv_obj_set_pos(hole_, static_cast<int>(s.hole_x - 17), static_cast<int>(s.hole_y - 17));
    lv_obj_set_pos(marble_, static_cast<int>(s.marble_x - 11), static_cast<int>(s.marble_y - 11));
    lv_label_set_text_fmt(score_, "%u", static_cast<unsigned>(s.score));
    if (imu_available_ != s.imu_available) { imu_available_ = s.imu_available; lv_label_set_text(hint_, imu_available_ ? "倾斜控制" : "倾斜不可用 · 触摸控制"); }
}
void GravityMazeContent::detach() noexcept { board_ = ring_ = hole_ = marble_ = score_ = hint_ = nullptr; }
}
