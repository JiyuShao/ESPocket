# 03 — 证明 baseline 启动稳定性

**What to build:** 一个可审查的 M1 candidate，能在冷启动与软件复位路径中重复到达产品 UI。

**Blocked by:** 02 — 通过 System Core 启动 Circular Shell。

**Status:** retrospective-resolved

- [x] 5 次冷启动通过。
- [x] 10 次 EN/software reset 通过。
- [x] 未观察到 panic、watchdog、assert 或 heap corruption。

## Resolution

已于 2026-09-25 接受；时间与观察保存在 M1 record 中。
