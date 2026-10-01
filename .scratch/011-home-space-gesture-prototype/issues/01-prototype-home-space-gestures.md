# 01 — 构建并验证 Home Space 真机交互样机

**What to build:** 可回退的 Launcher 列表和 Home Space 返回真机样机。

**Blocked by:** 实现无依赖；M7 acceptance 仍由 M6 `PASS` 阻塞。

**Status:** ready-for-human

## Acceptance Criteria

- [ ] Launcher 是可滚动的纵向 App 列表。
- [ ] 顶部下拉显示方向和阈值反馈，超过阈值松手回表盘且不点击 App。
- [ ] Quick Settings 上滑、左右 Card 反向横滑返回表盘。
- [ ] Shell 常驻顶部状态栏已移除；PWR 与息屏恢复仍符合原规则。
- [ ] 固件构建成功并在设备上记录操作结果与失败项。

## Comments

2026-09-30：这是可回退样机；不改变 M7 的计划状态。App Card 留待后续。

2026-09-30：增强版样机已构建并刷入真机，镜像 identity 和静态检查见 [M7 阶段外记录](../../../docs/milestones/m7/records/2026-09-30-home-space-prototype.md)。等待用户观察列表滚动、顶部下拉与 Quick Settings 返回后，再判断验收项。
