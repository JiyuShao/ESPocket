# 03 — 执行 M7 navigation hardware acceptance

**What to build:** Cards、Quick Settings、子页面 Back、Root 无 Back、PWR Home、gesture 与真实 Wi-Fi/brightness 效果的真机证明。

**Blocked by:** M6 `PASS`；02 — 关闭 M7 source 与 build gate。

**Status:** ready-for-human

- [x] 完整导航闭环通过 2 次（样机镜像；见 M7 两轮记录）。
- [x] Wi-Fi 与 brightness 各自真实改变状态 2 次（采集窗口累计；见 M7 两轮记录）。
- [ ] 所有单次 source、gesture、Home 与 failure 检查通过。

## Comments

- 2026-10-01：原任务包含「Back、直接 Launch Source」真机证明。根据 [ADR-0011](../../../docs/adr/0011-app-root-has-no-back.md)，改为子页面 Back、Root 无 Back 与 PWR Home；原要求保存在此作为决策历史。
- 2026-10-02：用户在多轮操作均正常后要求减少重复验收。固定次数从 5 降为 2，证据见 [两轮记录](../../../docs/milestones/m7/records/2026-10-02-two-navigation-loops.md)；单次路径覆盖与最终镜像核对仍保留。
