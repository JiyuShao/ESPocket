# 06 — 接入官方 Settings 的系统确认弹窗

**What to build:** 在既有 System Service 与 Shell Overlay 边界实现官方 Settings 所需的 Message Dialog 能力，保留 Settings 的确认/取消业务与导航事实源。

**Blocked by:** 无；先检查锁定 Core 的 dialog hook 与 Shell Overlay 生命周期。

**Status:** resolved

- [x] 复现 settings.display.light 提示 Message dialog is not supported by this system，确认实际 Owner seam。
- [x] 支持显示、更新、关闭与按钮结果，App 停止/Home 时取消并清理；不创建第二套 App 页面栈。
- [x] 补充当前缺失实现失败的回归，以及生命周期和结果归属检查。
- [x] 完整构建与自动导航通过；仅必要的确认/取消业务真机验收。

来源是 [2026-10-03 Sound 修复记录](../records/2026-10-03-settings-controls-rendering.md) 中附带观察的真实失败。004/05 的滑块验收不能关闭这张票。

## Comments

2026-10-03：普通镜像自动点击 Light 再次复现原错误。ESPocket System 实现公开 dialog hooks，Circular Shell 提供圆屏 modal 呈现；按钮/超时在 Shell App 任务交回 Core，Core 继续持有请求队列、归属与 App 停止清理。主机执行真实 Shell 呈现方法，覆盖错误 owner、旧请求、更新失败保留旧 UI、双击只交付一次、超时和停止丢弃待决选择；完整构建与设备门槛尚待完成。

2026-10-03 更新：完整构建、合成触摸的 Later、PWR Home 清理、确认重启与 Dark 恢复均通过，见[缺陷与修正版记录](../records/2026-10-03-display-glyph-theme-defects.md)。剩余一次必要可读性观察，未声明实体触摸门槛通过。

## Resolution

2026-10-03：`c21fec136` 完整构建、主机检查和真实设备合成输入通过 Later、PWR Home 清理、确认重启、Dark 持久恢复与重新进入 Settings。按钮结果交给 Core 后由官方 Settings 调用 HAL restart，没有复制主题或页面 Owner。用户确认 Settings 深色显示正常。该票的业务真机路径由自动重放完成，不声称物理触摸硬件已由该重放验证；Store 背景和返回字形由 09/011 单独验收。具体身份与限制见[记录](../records/2026-10-03-display-glyph-theme-defects.md)。
