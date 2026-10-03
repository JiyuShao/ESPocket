# 10 — Home Space 主题与紧凑弹窗

**What to build:** Watch Face、Launcher、Quick Settings 与 Shell 自有 Card 使用系统 Light/Dark；缩小确认弹窗的空白占比，确保浅色背景上的按钮可辨认。App Card 的颜色由 App 使用主题引用适配，不强制重写任意 App 颜色。

**Blocked by:** 修正版完整构建与有限设备观察；用户已明确为 Store 启动提示与系统弹窗按钮；两者使用同一 Message Dialog 呈现。

**Status:** ready-for-agent

- [x] Shell 固定颜色改为产品主题引用；保留深色原配色，浅色使用浅背景与深文字。
- [x] 弹窗按内容高度呈现，正文限高并可滚动，按钮显式不透明，保留请求归属与 Home 清理。
- [x] 旧弹窗源码在新布局回归中失败；实际呈现源码与 Shell 主题引用契约通过主机测试。
- [ ] 完整构建、确认/取消与 Light/Dark 有限视觉观察通过。
- [x] 确认 Store 网络/列表提示使用同一呈现；Native/Runtime 参考 App Card 改用主题样式，接入说明完整。
- [ ] Runtime Card 新包实际安装后的主题观察（当前只构建，不覆盖设备文件系统）。

旧 06 的请求生命周期验收和 09 的官方 Settings/Store 主题验收仍是历史事实。此票承接用户后续报告的布局、对比度与 Home Space 新范围；亮度卡死由 [08](08-fix-settings-brightness-freeze.md) 持有。

证据与限制见[本轮记录](../records/2026-10-03-shell-theme-dialog-followup.md)。
