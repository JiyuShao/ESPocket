# 02 — 构建 brightness semantic Adapter

**What to build:** Brightness Context、Action 与 Event 通过 Brookesia 公开接口使用真实 selected Display output。

**Blocked by:** [01 Semantic Registration](01-define-semantic-registration-contract.md)；[007/01 brightness output identity](../../007-m7-navigation/issues/01-fix-brightness-output-identity.md)（已完成）。

**Status:** resolved

- [x] Read 与 absolute set 报告实际观察到的 brightness。
- [x] UI 与 Assistant 共享语义，同时保留 caller identity。
- [x] 不存在重复 brightness state 或直接 HAL access。

## Resolution

源码、host contract 与完整独立固件构建通过。设备上的 Assistant 暂不准入，后续 03–04 接通已确认用户目标。证据见 [实现记录](../records/2026-10-03-semantic-brightness.md)。
