#include "product_fonts.hpp"

#include <exception>
#include <algorithm>

#include "brookesia/gui_lvgl/backend.hpp"
#include "esp_lv_adapter.h"

extern const unsigned char espocket_cjk_start[] asm("_binary_espocket_cjk_otf_start");
extern const unsigned char espocket_cjk_end[] asm("_binary_espocket_cjk_otf_end");

namespace espocket {
namespace {

class AdapterLock final {
public:
    AdapterLock() : result_(esp_lv_adapter_lock(-1)) {}
    ~AdapterLock() { if (result_ == ESP_OK) esp_lv_adapter_unlock(); }
    AdapterLock(const AdapterLock &) = delete;
    AdapterLock &operator=(const AdapterLock &) = delete;
    bool acquired() const { return result_ == ESP_OK; }

private:
    esp_err_t result_;
};

}

std::expected<std::unique_ptr<ProductFonts>, std::string> ProductFonts::create()
{
    AdapterLock lock;
    if (!lock.acquired()) {
        return std::unexpected("Failed to lock LVGL for product fonts");
    }
    auto fonts = std::unique_ptr<ProductFonts>(new ProductFonts());
    const auto data_size = reinterpret_cast<uintptr_t>(espocket_cjk_end) -
                           reinterpret_cast<uintptr_t>(espocket_cjk_start);
    const std::array<const lv_font_t *, 7> latin_fonts{
        &lv_font_montserrat_10, &lv_font_montserrat_12, &lv_font_montserrat_14,
        &lv_font_montserrat_16, &lv_font_montserrat_18, &lv_font_montserrat_20,
        &lv_font_montserrat_32};
    constexpr std::array<int32_t, 7> latin_sizes{10, 12, 14, 16, 18, 20, 32};
    for (size_t index = 0; index < sizes_.size(); ++index) {
        fonts->fonts_[index] = lv_tiny_ttf_create_data_ex(
            espocket_cjk_start, data_size, sizes_[index], LV_FONT_KERNING_NONE,
            sizes_[index] <= 24 ? 96 : sizes_[index] <= 40 ? 48 : 16);
        if (fonts->fonts_[index] == nullptr) {
            return std::unexpected("Failed to create zh_CN font size " + std::to_string(sizes_[index]));
        }
        size_t latin_index = 0;
        for (size_t candidate = 0; candidate < latin_sizes.size(); ++candidate) {
            if (latin_sizes[candidate] <= sizes_[index]) latin_index = candidate;
        }
        fonts->default_fonts_[index] = *latin_fonts[latin_index];
        fonts->default_fonts_[index].fallback = fonts->fonts_[index];
        const auto ascent = std::max(
            fonts->default_fonts_[index].line_height - fonts->default_fonts_[index].base_line,
            fonts->fonts_[index]->line_height - fonts->fonts_[index]->base_line);
        const auto descent = std::max(fonts->default_fonts_[index].base_line, fonts->fonts_[index]->base_line);
        fonts->default_fonts_[index].base_line = descent;
        fonts->default_fonts_[index].line_height = ascent + descent;
    }
    return fonts;
}

ProductFonts::~ProductFonts()
{
    AdapterLock lock;
    if (!lock.acquired()) std::terminate();
    for (auto *font : fonts_) {
        if (font != nullptr) lv_tiny_ttf_destroy(font);
    }
}

std::expected<void, std::string> ProductFonts::register_with(
    esp_brookesia::gui::lvgl::Backend &backend) const
{
    esp_brookesia::gui::RuntimeFontResource resource;
    resource.id = "zh_CN";
    resource.primary_src = "zh_CN";
    resource.languages = {"zh_CN"};
    resource.native_fonts.reserve(sizes_.size());
    for (size_t index = 0; index < sizes_.size(); ++index) {
        resource.native_fonts.push_back({reinterpret_cast<uintptr_t>(fonts_[index]), sizes_[index]});
    }
    if (!backend.register_font_resource(resource)) {
        return std::unexpected("Failed to register product font zh_CN");
    }
    resource.id = "default";
    resource.primary_src = "default";
    resource.languages = {"en", "zh_CN"};
    resource.native_fonts.clear();
    for (size_t index = 0; index < sizes_.size(); ++index) {
        resource.native_fonts.push_back({reinterpret_cast<uintptr_t>(&default_fonts_[index]), sizes_[index]});
    }
    if (!backend.register_font_resource(resource)) {
        return std::unexpected("Failed to register product default font");
    }
    return {};
}

}
