# 02 — 构建 brightness semantic Adapter

**What to build:** Brightness Context、Action 与 Event 通过 Brookesia 公开接口使用真实 selected Display output。

**Blocked by:** [01 Semantic Registration](01-define-semantic-registration-contract.md)；[007/01 brightness output identity](../../007-m7-navigation/issues/01-fix-brightness-output-identity.md)（已完成）。

**Status:** ready-for-agent

- [ ] Read 与 absolute set 报告实际观察到的 brightness。
- [ ] UI 与 Assistant 共享语义，同时保留 caller identity。
- [ ] 不存在重复 brightness state 或直接 HAL access。
