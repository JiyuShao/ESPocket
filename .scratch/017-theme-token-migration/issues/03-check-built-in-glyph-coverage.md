# 03 — 校验内置字体字形覆盖

**What to build:** 修复 Launcher 箭头方框，并在维护资源和有效固件配置上静态校验字体字形覆盖。

**Blocked by:** 完整构建及单次像素确认。

**Status:** ready-for-agent

- [x] 用实际字体选择规则和 cmap 重现 16sp 箭头缺失，修复为已启用的 18sp。
- [x] 静态检查维护 JSON literal label、styleRefs 与继承字号，报告文件、节点、码点和实际字体。
- [x] 统一主机测试及独立构建的有效 sdkconfig 门槛接入，未知 cmap 或无法解析的字号不得静默通过。
- [ ] 完整构建、刷写与单次箭头像素确认记入记录。

## Comments

此次新 Launcher chevron 明确请求 16sp；产品启用 Montserrat 18/20/32，无更小字号时 GUI 回退到 UNSCII 8，缺少 U+F054。检查以实际 LVGL cmap 为准，不凭图标名称或源码注释判断。动态文本、文件字体和外部 App 不在本静态门槛覆盖内。

构建、刷写与有效配置证据见[字形记录](../records/2026-10-04-glyph-coverage.md)；实际像素确认仍待用户。
