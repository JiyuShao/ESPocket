# 05 — 验证 cancellation 与 result 语义

**What to build:** Brightness tracer bullet 在 UI 与 Assistant caller 中区分 canceled-before-submit、committed、failed 与 uncertain 结果。

**Blocked by:** 04 — 执行 user-goal authorization。

**Status:** ready-for-agent

- [ ] PWR 或 caller cancellation 阻止尚未提交的工作。
- [ ] 已提交工作通过观察确认，不假定已回滚。
- [ ] 测试覆盖 Event delivery 与 Owner failure。
