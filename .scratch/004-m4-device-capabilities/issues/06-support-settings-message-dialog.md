# 06 — 接入官方 Settings 的系统确认弹窗

**What to build:** 在既有 System Service 与 Shell Overlay 边界实现官方 Settings 所需的 Message Dialog 能力，保留 Settings 的确认/取消业务与导航事实源。

**Blocked by:** 无；先检查锁定 Core 的 dialog hook 与 Shell Overlay 生命周期。

**Status:** ready-for-agent

- [ ] 复现 settings.display.light 提示 Message dialog is not supported by this system，确认实际 Owner seam。
- [ ] 支持显示、更新、关闭与按钮结果，App 停止/Home 时取消并清理；不创建第二套 App 页面栈。
- [ ] 补充当前缺失实现失败的回归，以及生命周期和结果归属检查。
- [ ] 完整构建与自动导航通过；仅必要的确认/取消业务真机验收。

来源是 [2026-10-03 Sound 修复记录](../records/2026-10-03-settings-controls-rendering.md) 中附带观察的真实失败。004/05 的滑块验收不能关闭这张票。
