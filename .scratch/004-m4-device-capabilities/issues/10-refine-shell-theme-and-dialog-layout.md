# 10 — Home Space 主题与紧凑弹窗

**What to build:** Watch Face、Launcher、Quick Settings 与 Shell 自有 Card 使用系统 Light/Dark；缩小确认弹窗的空白占比，确保浅色背景上的按钮可辨认。App Card 的颜色由 App 使用主题引用适配，不强制重写任意 App 颜色。

**Blocked by:** None.

**Status:** resolved

- [x] Shell 固定颜色改为产品主题引用；保留深色原配色，浅色使用浅背景与深文字。
- [x] 弹窗按内容高度呈现，正文限高并可滚动，按钮显式不透明，保留请求归属与 Home 清理。
- [x] 旧弹窗源码在新布局回归中失败；实际呈现源码与 Shell 主题引用契约通过主机测试。
- [x] 完整构建、确认/取消与 Light/Dark 有限视觉观察通过。
- [x] 确认 Store 网络/列表提示使用同一呈现；Native/Runtime 参考 App Card 改用主题样式，接入说明完整。
- [x] Runtime Card 新资源实际部署，Light/Dark 打开与 Back/Home 自动回归通过；用户确认浅色 Card 清楚正常。

旧 06 的请求生命周期验收和 09 的官方 Settings/Store 主题验收仍是历史事实。此票承接用户后续报告的布局、对比度与 Home Space 新范围；亮度卡死由 [08](08-fix-settings-brightness-freeze.md) 持有。

证据与限制见[本轮记录](../records/2026-10-03-shell-theme-dialog-followup.md)。

2026-10-03 收尾：默认 production 74b1b55ce 已完整构建、刷入及启动；新版 Runtime Card 资源已在保留其他文件的备份镜像中部署。App 自动回归、Later/Home 与 Dark 确认重启恢复通过，视觉仍独立等待，不以快照代替像素。另一聊天的 017 主题变量迁移未混入本次镜像。证据见 [默认构建收尾](../records/2026-10-03-production-followup.md)。

用户确认深色弹窗“基本正常”、浅色“正常，浅色按钮清楚”；确认/取消/重启恢复均有自动证据。问号为当前 Question 的文本图标呈现，作为后续样式改进记录，不是缺失字形或报错。

## Resolution

2026-10-04：Runtime Card 新资源已部署到保留其他文件的设备镜像；在 Dark/Light 两种模式实际打开 Root/Detail、Back/Home 均通过，用户确认浅色“正常，Card 显示清楚”。结合已接受的两种主题弹窗布局/按钮、完整构建和主题确认/取消，关闭 10。当前 Question 的问号文本图标有后续美观改进空间；017 正在另一聊天独立推进，没有混入本次产物。
