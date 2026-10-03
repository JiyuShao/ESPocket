# 2026-10-04 — Launcher 箭头与内置字体覆盖

## 故障与修复

新 Launcher row 的 U+F054 请求 16sp，而有效配置只有 Montserrat 18/20/32。真实 GUI 的 get_builtin_font 选最近的不大于目标的启用字号；没有更小字号时退回 UNSCII 8，它不包含箭头。静态检查在原资源上明确报告四个节点、两种主题缺字；改为 18sp 后通过。

新增 scripts/firmware/check_glyphs.py 从真实 LVGL cmap 读取覆盖，检查维护 JSON literal label、styleRefs、继承字号与有效 sdkconfig。主机测试还编译实际 get_builtin_font 对照字号选择。未知 cmap 或无法解析的字号不静默通过；动态文本、外部 App 与文件字体仍需各自覆盖检查。

## 构建与设备

- 主机字形回归 4 tests PASS，实际有效 sdkconfig 字形检查 PASS。
- 独立完整 store-candidate 构建完成，七个组件 source/patch hash 校验通过；默认字体显式设为既有 UNSCII 8，HTTP 仍为 1 worker / 1 request。
- 首个候选 5d6de3fd8，随后触摸松手清理修复完整构建为 5bb555ca5；只写应用分区 0x60000，flash hash verify 通过，设备 hello identity 一致。
- 最终 ELF SHA-256：5bb555ca59e3828b18496e8d02f8268092f0c7e78e31dbe398a815391da27952。
- 最终 BIN SHA-256：4433744019dd77fcaa2c1a0d922bfa3e12967f125f73d094a2d03b831db18c38。
- 产物保留 /private/tmp/espocket-store-release-5bb555ca5；静态字形覆盖不能替代屏幕像素确认，单次实际箭头观察仍待用户。
