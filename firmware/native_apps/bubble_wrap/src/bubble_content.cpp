// SPDX-License-Identifier: MIT
#include "bubble_content.hpp"
namespace espocket {
std::expected<void, std::string> BubbleContent::attach(lv_obj_t *root)
{
    auto *board = lv_obj_create(root);
    if (!board) return std::unexpected("Board allocation failed");
    lv_obj_remove_style_all(board);
    lv_obj_set_size(board, 466, 466);
    lv_obj_center(board);
    lv_obj_remove_flag(board, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_remove_flag(board, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_set_style_bg_color(board, lv_color_hex(0x101014), 0);
    lv_obj_set_style_bg_opa(board, LV_OPA_COVER, 0);
    bubble::Model model;
    for (const auto &cell : model.cells()) {
        auto *obj = lv_obj_create(board);
        if (!obj) return std::unexpected("Bubble allocation failed");
        lv_obj_remove_style_all(obj);
        lv_obj_remove_flag(obj, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_remove_flag(obj, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_set_style_bg_opa(obj, LV_OPA_COVER, 0);
        lv_obj_set_pos(obj, cell.x - 39, cell.y - 39);
        cells_.push_back(obj);
    }
    painted_.assign(cells_.size(), true);
    label_ = lv_label_create(board);
    if (!label_) return std::unexpected("Count allocation failed");
    lv_obj_set_style_text_font(label_, &lv_font_montserrat_16, 0);
    lv_obj_set_style_text_color(label_, lv_color_hex(0x6A7486), 0);
    lv_obj_align(label_, LV_ALIGN_CENTER, 0, 196);
    paint(model);
    return {};
}
void BubbleContent::paint(const bubble::Model &model)
{
    if (!label_ || cells_.size() != model.cells().size()) return;
    for (size_t i = 0; i < cells_.size(); ++i) {
        const bool popped = model.cells()[i].popped;
        if (painted_[i] == popped) continue;
        painted_[i] = popped;
        auto *obj = cells_[i];
        const int size = popped ? 54 : 78;
        lv_obj_set_size(obj, size, size);
        // Keep the original top-left anchor when shrinking a popped bubble.
        lv_obj_set_style_radius(obj, size / 2, 0);
        lv_obj_set_style_bg_color(obj, lv_color_hex(popped ? 0x23262E : 0xA8C2E0), 0);
        lv_obj_set_style_bg_grad_color(obj, lv_color_hex(0x53709A), 0);
        lv_obj_set_style_bg_grad_dir(obj, popped ? LV_GRAD_DIR_NONE : LV_GRAD_DIR_VER, 0);
        lv_obj_set_style_border_width(obj, 0, 0);
    }
    if (remaining_ != model.remaining()) {
        remaining_ = model.remaining(); lv_label_set_text_fmt(label_, "%d", remaining_);
    }
}
void BubbleContent::detach() noexcept { cells_.clear(); painted_.clear(); label_ = nullptr; remaining_ = -1; }
}
