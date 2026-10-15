#include "ble_remote_content.hpp"
namespace espocket {
std::expected<void, std::string> BleRemoteContent::attach(lv_obj_t *root)
{
    root_ = lv_obj_create(root); if (!root_) return std::unexpected("Remote board allocation failed");
    lv_obj_remove_style_all(root_); lv_obj_set_size(root_, 466, 466); lv_obj_center(root_);
    lv_obj_set_style_bg_color(root_, lv_color_hex(0x101014), 0); lv_obj_set_style_bg_opa(root_, LV_OPA_COVER, 0);
    title_ = lv_label_create(root_); status_ = lv_label_create(root_); hint_ = lv_label_create(root_);
    if (!title_ || !status_ || !hint_) return std::unexpected("Remote label allocation failed");
    lv_obj_set_style_text_color(title_, lv_color_white(), 0); lv_obj_set_style_text_color(status_, lv_color_hex(0xE0B33A), 0); lv_obj_set_style_text_color(hint_, lv_color_hex(0xA8B0C0), 0);
    lv_obj_align(title_, LV_ALIGN_CENTER, 0, -76); lv_obj_align(status_, LV_ALIGN_CENTER, 0, -26); lv_obj_align(hint_, LV_ALIGN_CENTER, 0, 34);
    lv_label_set_text(title_, "触控板"); lv_label_set_text(status_, "BLE HID 不可用"); lv_label_set_text(hint_, "点击上方切换空中鼠标"); return {};
}
void BleRemoteContent::paint(const hid::MouseModel &model, bool endpoint_available, bool connected)
{
    if (!title_) return;
    const bool air = model.state().mode == hid::Mode::air;
    lv_label_set_text(title_, air ? "空中鼠标" : "触控板");
    lv_label_set_text(status_, !endpoint_available ? "BLE HID 不可用" : (connected ? "已连接" : "等待配对"));
    lv_label_set_text(hint_, air ? (model.state().imu_available ? "倾斜移动 · 点击切回触控板" : "IMU 不可用 · 触摸点击") : "内圈移动 · 外圈滚轮 · 双指右键");
}
void BleRemoteContent::detach() noexcept { root_ = title_ = status_ = hint_ = nullptr; }
}
