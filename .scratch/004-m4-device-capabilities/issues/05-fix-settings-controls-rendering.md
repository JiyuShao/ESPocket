# 05 — 修复官方 Settings 控件渲染

**What to build:** 在真实 Brookesia GUI Owner 与 ESPocket System 装配边界修复 Sound 页 Volume/开关缺失；不复制官方 Settings 页面或导航。

**Blocked by:** 无；先区分主题未注册与控件几何尺寸，再做最小修复。

**Status:** resolved

- [x] 在当前候选复现用户照片中的控件缺失，记录真实 GUI frame 与主题解析结果。
- [x] 补充准确的回归门槛，再修复实际 Owner；如维护上游补丁，按 ADR-0016 锁定源码和 patch hash。
- [x] 完整构建、启动与自动导航通过，不手改原始 managed_components。
- [x] 真机 Sound 页显示可操作 Volume 与 Mute；用户只需验证一次。

诊断证据见 [2026-10-03 记录](../records/2026-10-03-settings-controls-rendering.md)。这张票不关闭 Audio 的实际听感门槛。

## Resolution

2026-10-03：锁定 Core embedded-theme seam、产品主题与 Settings 圆屏资源补丁完成；79 项 host tests、完整候选构建、启动与 34 步导航通过。用户在 image `8b69429a1` 确认 Volume/Mute 可见、拖动正常，串口真实 volume 更新对应。准确身份与证据见上述记录；不关闭 Audio 听感或其他 Settings 弹窗问题。
