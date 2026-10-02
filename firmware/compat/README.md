# 上游兼容实现

compat 是 compatibility 的缩写。本目录保存 ESPocket 自有的兼容头文件与编译适配；修改上游源码的 diff 放在[patches](../patches/README.md)。这是项目约定，不是强制行业目录规范。

## 当前实现

| 文件 | 适用范围 | 移除条件 |
|---|---|---|
| [Backlight 类型兼容](brookesia_hal_custom_0_1_backlight.hpp) | Waveshare brookesia_hal_custom 0.1.0 与 Brookesia HAL 0.8.x | 板包使用官方 BacklightIface/LCD_GROUP_ID，且无强制 include 时构建通过 |
| [Picolibc noreturn 属性兼容](idf_6_0_1_picolibc_noreturn.hpp) | ESP-IDF 6.0.1、GCC 15.2 Picolibc、C++23 | 锁定工具链的受影响 display/audio board-header 翻译单元可在原告警门槛下构建，不需强制 include |

每项注明影响版本、作用范围、问题来源及删除条件。CMake 只向受影响目标/翻译单元注入兼容实现，按实际约束保持告警门槛。升级依赖后复核这些条件，不把历史构建通过当作新版本适用证明。

源码核查、故障原因与验收证据放在[对应 Effort](../../.scratch/README.md) 的 records，由该 Effort 的工作票引用。
