# 01 — 迁移现有界面并验证主题契约

**What to build:** 将产品维护的 Shell、Hello 页面与 Card、系统键盘、消息弹窗及 Back 控件统一接入产品主题。

**Blocked by:** None.

**Status:** resolved

- [x] Shell 使用语义样式，不再按旧十六进制色值命名；两种模式保持 Card 颜色含义。
- [x] Hello 完整页面与 Card 无普通界面的固定颜色。
- [x] 原生键盘、弹窗、Back 与 Card hint 使用产品主题，颜色查询不发生在 LVGL 锁内。
- [x] 新增引用在 light/dark 中完整定义，常用文字颜色对比度至少 4.5:1。
- [x] 统一 host checks、Runtime package build 与独立固件构建通过。

## Comments

2026-10-03：用户要求按刚建立的主题规范迁移现有页面。源码与构建验收由本票持有；不自动刷写设备。真机视觉结果保持未验证，不以 host 对比度计算替代像素检查。

## Resolution

源码迁移、统一 host checks、Runtime package build、原生主题行为测试与独立生产配置固件构建全部通过。构建输入、固件 identity 和未验证的真机画面见[迁移记录](../records/2026-10-03-theme-migration.md)。
