# 2026-10-04 — 主题与字形剩余证据核查

本线仅检查捕获的源码与历史记录，不访问设备。结果来自隔离 baseline，不代表原 checkout 的集成状态。

## 已有有效证据

[主题部署记录](2026-10-04-theme-deployment.md) 已保存 light Native/Runtime 按钮普通态与旧系统配色的用户确认。普通固件 24acc698e 完整构建、刷写 hash 和新版布局合成输入回归通过，但新版黄色 Brightness 按钮、双列 Quick Settings 与紧凑 Launcher 的最终像素反馈未记入。

[字形记录](2026-10-04-glyph-coverage.md) 已保存 18sp 的 U+F054 修复、真实 LVGL cmap/有效配置门槛、5bb555ca5 构建与刷写校验。静态覆盖不证明箭头在最终 Launcher 布局正确显示。

[截图记录](../../012-test-automation-contract/records/2026-10-04-rendered-frame-screenshot.md) 的最新 f3fdd7e82 成功导出 Store 列表、Local Loading 与 Local 扫描完成三个 466×466 rendered-frame。这些画面不覆盖 Home Space、普通态 Hello 按钮或 Launcher 箭头，不证明实体面板。较早失败与部分传输没有被当作完整截图证据。

## 最终仍缺

- 在同一最终普通集成镜像上记录 image identity、Runtime 资源身份和 light/dark 恢复状态，再分别观察 Hello Native/Runtime 按钮普通态与按下态。
- light/dark 新版 Watch Face、Brightness 黄色按钮、双列 Quick Settings、动态 Launcher 行与箭头：最终 rendered-frame 可定位软件像素，但物理面板单次观察仍独立。
- U+F054 单次实际箭头像素确认；已有完整构建/刷写证据可引用，不把整条条件重复作新实现，也不凭历史部署关闭剩余条件。

017/02、03 保持开放；本线不新增刷写、串口占用或设备状态改变。即时主题切换依旧属于 019/10，不能把重启恢复主题当作即时切换验收。
