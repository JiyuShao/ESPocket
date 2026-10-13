// SPDX-License-Identifier: MIT
#include "brick_content.hpp"
#include <cmath>
namespace espocket {
namespace {
lv_obj_t *shape(lv_obj_t *parent)
{
    auto *obj = lv_obj_create(parent);
    if (obj) {
        lv_obj_remove_style_all(obj);
        lv_obj_remove_flag(obj, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_remove_flag(obj, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_set_style_bg_opa(obj, LV_OPA_COVER, 0);
    }
    return obj;
}
void visibility(lv_obj_t *obj, bool visible)
{
    if (visible) lv_obj_remove_flag(obj, LV_OBJ_FLAG_HIDDEN);
    else lv_obj_add_flag(obj, LV_OBJ_FLAG_HIDDEN);
}
void put(lv_obj_t *obj, float x, float y, int diameter)
{
    lv_obj_set_pos(obj, static_cast<int>(x - diameter / 2), static_cast<int>(y - diameter / 2));
}
lv_obj_t *arc(lv_obj_t *parent, int width, uint32_t color)
{
    auto *obj = lv_arc_create(parent);
    if (!obj) return nullptr;
    lv_obj_remove_style_all(obj); lv_obj_remove_flag(obj, LV_OBJ_FLAG_CLICKABLE);
    const int diameter = 2 * (brick::paddle_radius + brick::ball_radius + width);
    lv_obj_set_size(obj, diameter, diameter); lv_obj_center(obj); lv_arc_set_value(obj, 0);
    lv_obj_set_style_arc_width(obj, width, LV_PART_MAIN);
    lv_obj_set_style_arc_color(obj, lv_color_hex(color), LV_PART_MAIN);
    return obj;
}
}
std::expected<void, std::string> BrickContent::attach(lv_obj_t *root)
{
    auto *board = shape(root);
    if (!board) return std::unexpected("Board allocation failed");
    lv_obj_set_size(board, brick::canvas_size, brick::canvas_size); lv_obj_center(board);
    lv_obj_set_style_bg_color(board, lv_color_hex(0x101014), 0);
    for (auto &obj : bricks_) {
        obj = shape(board); if (!obj) return std::unexpected("Brick allocation failed");
        lv_obj_set_style_radius(obj, 4, 0); lv_obj_set_style_border_side(obj, LV_BORDER_SIDE_FULL, 0);
        lv_obj_set_style_border_color(obj, lv_color_white(), 0); lv_obj_set_style_border_opa(obj, LV_OPA_COVER, 0);
    }
    auto *wall = arc(board, 4, 0x3A3A46);
    if (!wall) return std::unexpected("Wall allocation failed");
    lv_arc_set_bg_angles(wall, 150, 30);
    paddle_ = arc(board, 16, 0xFFFFFF);
    if (!paddle_) return std::unexpected("Paddle allocation failed");
    for (auto &obj : obstacles_) {
        obj = shape(board); if (!obj) return std::unexpected("Obstacle allocation failed");
        lv_obj_set_size(obj, 26, 26); lv_obj_set_style_radius(obj, LV_RADIUS_CIRCLE, 0);
        lv_obj_set_style_bg_color(obj, lv_color_hex(0xE05070), 0);
    }
    ball_ = shape(board);
    if (!ball_) return std::unexpected("Ball allocation failed");
    lv_obj_set_size(ball_, 16, 16); lv_obj_set_style_radius(ball_, LV_RADIUS_CIRCLE, 0);
    lv_obj_set_style_bg_color(ball_, lv_color_white(), 0);
    score_ = lv_label_create(board); ready_ = lv_label_create(board);
    if (!score_ || !ready_) return std::unexpected("Label allocation failed");
    // Inherit the product default font from the JSON Container (Latin with Chinese fallback).
    lv_obj_set_style_text_color(score_, lv_color_white(), 0);
    lv_obj_set_style_text_color(ready_, lv_color_hex(0xE8ECF0), 0);
    paint(brick::Model{});
    return {};
}
void BrickContent::paint(const brick::Model &model)
{
    if (!score_ || !ready_ || !ball_ || !paddle_) return;
    const auto &s = model.state();
    const bool rebuild = !painted_ || painted_->level != s.level || painted_->brick_count != s.brick_count;
    for (int i = 0; i < brick::max_bricks; ++i) {
        const auto &b = s.bricks[i];
        if (rebuild) {
            lv_obj_set_pos(bricks_[i], b.x1, b.y1); lv_obj_set_size(bricks_[i], b.x2 - b.x1, b.y2 - b.y1);
            lv_obj_set_style_bg_color(bricks_[i], lv_color_hex(b.color), 0);
        }
        if (rebuild || painted_->bricks[i].hp != b.hp) {
            visibility(bricks_[i], b.hp > 0); lv_obj_set_style_border_width(bricks_[i], b.hp > 1 ? 3 : 0, 0);
        }
    }
    if (!painted_ || painted_->paddle_angle != s.paddle_angle || painted_->paddle_half != s.paddle_half) {
        const float a = s.paddle_angle - 90;
        lv_arc_set_bg_angles(paddle_, static_cast<int>(a - s.paddle_half + 360) % 360,
            static_cast<int>(a + s.paddle_half) % 360);
    }
    if (!painted_ || painted_->x != s.x || painted_->y != s.y) put(ball_, s.x, s.y, 16);
    if (!painted_ || painted_->obstacle_step != s.obstacle_step || painted_->obstacle_angle != s.obstacle_angle) {
        for (size_t i = 0; i < obstacles_.size(); ++i) {
            visibility(obstacles_[i], s.obstacle_step > 0);
            const float a = (s.obstacle_angle + i * 180) * 0.0174533f;
            put(obstacles_[i], brick::center + std::sin(a) * 124, brick::center - std::cos(a) * 124, 26);
        }
    }
    if (!painted_ || painted_->level != s.level || painted_->remaining != s.remaining || painted_->lives != s.lives) {
        lv_label_set_text_fmt(score_, "第%d关  %d  生命%d", s.level + 1, s.brick_count - s.remaining, s.lives);
        lv_obj_align(score_, LV_ALIGN_CENTER, 0, 168);
    }
    if (!painted_ || painted_->phase != s.phase) {
        visibility(ready_, s.phase != brick::Phase::Playing);
        lv_label_set_text(ready_, s.phase == brick::Phase::Won ? "全部通关！点击重新开始" : "点击开始");
        lv_obj_align(ready_, LV_ALIGN_CENTER, 0, 128);
    }
    painted_ = s;
}
void BrickContent::detach() noexcept
{
    bricks_.fill(nullptr); obstacles_.fill(nullptr);
    paddle_ = ball_ = score_ = ready_ = nullptr; painted_.reset();
}
}
