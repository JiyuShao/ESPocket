# 01 — 构建并验证 Home Space 真机交互样机

**What to build:** 可回退的 Launcher 列表和 Home Space 返回真机样机。

**Blocked by:** None；正式导航验收由 [007/03](../../007-m7-navigation/issues/03-run-navigation-hardware-acceptance.md) 独立负责。

**Status:** ready-for-human

## Acceptance Criteria

- [x] Launcher 是可滚动的纵向 App 列表。
- [ ] 顶部下拉显示方向和阈值反馈，超过阈值松手回表盘且不点击 App。
- [x] Quick Settings 上滑、左右 Card 反向横滑返回表盘。
- [x] Shell 常驻顶部状态栏已移除；PWR 与息屏恢复仍符合原规则。
- [x] 固件构建成功并在设备上记录操作结果与失败项。

## Comments

2026-09-30：这是可回退样机；不改变 M7 的计划状态。App Card 留待后续。

2026-09-30：增强版样机已构建并刷入真机，镜像 identity 和静态检查见 [M7 阶段外记录](../records/2026-09-30-home-space-prototype.md)。等待用户观察列表滚动、顶部下拉与 Quick Settings 返回后，再判断验收项。

2026-10-03 对账：Quick Settings/Card/PWR/显示与构建条件复用已关闭的 [007/03](../../007-m7-navigation/issues/03-run-navigation-hardware-acceptance.md) 和 [013 集中 smoke](../../013-firmware-structure-refactor/records/2026-10-02-final-verification.md)，不要求重复。Launcher 顶部下拉回表盘与不误开 App 已接受；实际列表滚动范围、拉伸/箭头/阈值提示的明确观察尚缺，剩余两个 checklist 待一次集中反馈。

2026-10-03：用户确认“其他正常”，但返回箭头显示空心方块；列表条件接受，阈值反馈仍失败。已添加字体选择/字形覆盖 RED→GREEN 修正，完整构建通过，物理显示待验收；见[缺陷记录](../../004-m4-device-capabilities/records/2026-10-03-display-glyph-theme-defects.md)。
