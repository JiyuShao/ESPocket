#pragma once

#include <array>
#include <expected>
#include <memory>
#include <string>

#include "lvgl.h"

namespace esp_brookesia::gui::lvgl {
class Backend;
}

namespace espocket {

class ProductFonts final {
public:
    static std::expected<std::unique_ptr<ProductFonts>, std::string> create();
    ~ProductFonts();
    ProductFonts(const ProductFonts &) = delete;
    ProductFonts &operator=(const ProductFonts &) = delete;
    std::expected<void, std::string> register_with(esp_brookesia::gui::lvgl::Backend &backend) const;

private:
    ProductFonts() = default;
    static constexpr std::array<int32_t, 16> sizes_{10, 11, 12, 13, 14, 15, 16, 18, 20, 22, 24, 28, 32, 40, 48, 64};
    std::array<lv_font_t *, sizes_.size()> fonts_{};
};

}
