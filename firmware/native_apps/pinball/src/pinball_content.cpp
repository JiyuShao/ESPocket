// SPDX-License-Identifier: MIT
#include "pinball_content.hpp"
#include <cmath>
namespace espocket {
namespace {
lv_obj_t *shape(lv_obj_t *parent)
{
    auto *obj = lv_obj_create(parent);
    if (obj) { lv_obj_remove_style_all(obj); lv_obj_remove_flag(obj, LV_OBJ_FLAG_CLICKABLE); lv_obj_remove_flag(obj, LV_OBJ_FLAG_SCROLLABLE); lv_obj_set_style_bg_opa(obj, LV_OPA_COVER, 0); }
    return obj;
}
void put(lv_obj_t *obj, float x, float y, int d) { lv_obj_set_pos(obj, static_cast<int>(x - d / 2), static_cast<int>(y - d / 2)); }
void visible(lv_obj_t *obj, bool value) { if (value) lv_obj_remove_flag(obj, LV_OBJ_FLAG_HIDDEN); else lv_obj_add_flag(obj, LV_OBJ_FLAG_HIDDEN); }
}
std::expected<void, std::string> PinballContent::attach(lv_obj_t *root)
{
    auto *board = shape(root); if (!board) return std::unexpected("Board allocation failed");
    lv_obj_set_size(board, pinball::canvas_size, pinball::canvas_size); lv_obj_center(board);
    lv_obj_set_style_bg_color(board, lv_color_hex(0x101014), 0);
    auto *ring = lv_arc_create(board); if (!ring) return std::unexpected("Wall allocation failed");
    lv_obj_remove_style_all(ring); lv_obj_remove_flag(ring, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_set_size(ring, 424, 424); lv_obj_center(ring); lv_arc_set_value(ring, 0); lv_arc_set_bg_angles(ring, 102, 78);
    lv_obj_set_style_arc_width(ring, 6, LV_PART_MAIN); lv_obj_set_style_arc_color(ring, lv_color_hex(0x3A3A46), LV_PART_MAIN);
    constexpr uint32_t colors[pinball::bumper_count] = {0xE0B33A, 0x5BD48A, 0x7FB0FF, 0xE06FA0, 0x9A7BE0};
    for (int i = 0; i < pinball::bumper_count; ++i) {
        bumpers_[i] = shape(board); if (!bumpers_[i]) return std::unexpected("Bumper allocation failed");
        lv_obj_set_size(bumpers_[i], 42, 42); lv_obj_set_style_radius(bumpers_[i], LV_RADIUS_CIRCLE, 0); lv_obj_set_style_bg_color(bumpers_[i], lv_color_hex(colors[i]), 0);
    }
    for (auto &target : targets_) {
        target = shape(board); if (!target) return std::unexpected("Target allocation failed");
        lv_obj_set_size(target, 18, 18); lv_obj_set_style_radius(target, LV_RADIUS_CIRCLE, 0); lv_obj_set_style_bg_color(target, lv_color_hex(0xFFD24A), 0);
    }
    for (auto &flipper : flippers_) {
        flipper = lv_line_create(board); if (!flipper) return std::unexpected("Flipper allocation failed");
        lv_obj_remove_style_all(flipper); lv_obj_set_style_line_width(flipper, 14, 0); lv_obj_set_style_line_color(flipper, lv_color_white(), 0); lv_obj_set_style_line_rounded(flipper, true, 0);
    }
    ball_ = shape(board); score_ = lv_label_create(board); ready_ = lv_label_create(board);
    if (!ball_ || !score_ || !ready_) return std::unexpected("Ball or label allocation failed");
    lv_obj_set_size(ball_, 13, 13); lv_obj_set_style_radius(ball_, LV_RADIUS_CIRCLE, 0); lv_obj_set_style_bg_color(ball_, lv_color_white(), 0);
    lv_obj_set_style_text_color(score_, lv_color_white(), 0); lv_obj_set_style_text_color(ready_, lv_color_hex(0xE8ECF0), 0);
    paint(pinball::Model{}); return {};
}
void PinballContent::paint(const pinball::Model &model)
{
    if (!ball_ || !score_ || !ready_) return;
    const auto &s = model.state();
    const bool reset_board = !painted_ || painted_->phase != s.phase;
    for (int i = 0; i < pinball::bumper_count; ++i) { if (reset_board || !painted_ || painted_->bumper_x[i] != s.bumper_x[i]) put(bumpers_[i], s.bumper_x[i], s.bumper_y[i], 42); }
    for (int i = 0; i < pinball::target_count; ++i) { if (reset_board || !painted_ || painted_->target_x[i] != s.target_x[i] || painted_->target_up[i] != s.target_up[i]) { put(targets_[i], s.target_x[i], s.target_y[i], 18); visible(targets_[i], s.target_up[i]); } }
    if (!painted_ || painted_->x != s.x || painted_->y != s.y) put(ball_, s.x, s.y, 13);
    for (int i = 0; i < 2; ++i) {
        if (reset_board || !painted_ || painted_->flippers[i].angle != s.flippers[i].angle) {
            const float a = s.flippers[i].angle * 0.0174533f;
            points_[0] = {static_cast<lv_value_precise_t>(s.flippers[i].px), static_cast<lv_value_precise_t>(s.flippers[i].py)};
            points_[1] = {static_cast<lv_value_precise_t>(s.flippers[i].px + std::cos(a) * 104), static_cast<lv_value_precise_t>(s.flippers[i].py + std::sin(a) * 104)};
            lv_line_set_points(flippers_[i], points_.data(), 2);
        }
    }
    if (!painted_ || painted_->points != s.points || painted_->balls != s.balls) { lv_label_set_text_fmt(score_, "%d  球%d", s.points, s.balls); lv_obj_align(score_, LV_ALIGN_CENTER, 0, 116); }
    if (!painted_ || painted_->phase != s.phase) { visible(ready_, s.phase != pinball::Phase::Playing); lv_label_set_text(ready_, s.phase == pinball::Phase::GameOver ? "游戏结束，点击重新开始" : "点击开始"); lv_obj_align(ready_, LV_ALIGN_CENTER, 0, 168); }
    painted_ = s;
}
void PinballContent::detach() noexcept { bumpers_.fill(nullptr); targets_.fill(nullptr); flippers_.fill(nullptr); ball_ = score_ = ready_ = nullptr; painted_.reset(); }
}
