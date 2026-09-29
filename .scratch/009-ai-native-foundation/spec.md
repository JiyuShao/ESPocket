# AI Native foundation

Sequence: 009

Status: planned
Blocked by: M8 contract acceptance for product sequencing.

## Problem Statement

ESPocket 需要让 AI access 成为产品与架构设计的一部分，同时不创建第二套 state、authorization 或 lifecycle 系统。

## Solution

要求每个系统设计记录 Exposure Decision；通过真实 Owner 与 Brookesia 公开 seam 建立 brightness tracer bullet；再把已验证语义扩展到 App 与 Service capability。

## User Stories

1. 作为用户，我希望 Assistant action 代表我已经确认的目标。
2. 作为系统 Owner，我希望继续持有状态与副作用。
3. 作为 App author，我希望 semantic capability 具有明确 lifetime 与 permission。
4. 作为产品设计者，我希望每个新 capability 同时考虑 human 与 AI access。
5. 作为安全 reviewer，我希望 caller、grant、risk 与 framework admission 一起评估。
6. 作为 maintainer，我希望特定 Brookesia 版本细节封装在聚焦 Adapter 后。

## Implementation Decisions

- AI Native 是底层设计维度，不是 App type 或 manager layer。
- Context、Action 与 Event 在真实 Owner 边界注册。
- 必须具有 User Intent 或 Scoped Grant；App/Agent request 不构成 authority。
- App capability registration 属于一个 Running Instance。
- Brightness 是第一个 capability seam；抽象等待第二个真实 capability。

## Testing Decisions

- 从产品 UI 与 Assistant 调用同一 brightness semantic Action，并分别验证 caller authorization。
- 覆盖 read、set、Event、denied、canceled-before-submit、uncertain-after-submit 与 Owner failure 结果。
- 证明不存在重复 brightness state 或直接 HAL access。
- 第一条 seam 可信后，再增加 Native 与 Runtime lifecycle 测试。

## Out of Scope

选择 model provider、XiaoZhi/ESP-Claw 集成、全局 AI Manager、GUI automation，以及 M5 trust 通过前的 remote Runtime AI capability exposure。

## Tickets

- [01 — 定义 Semantic Registration 契约](issues/01-define-semantic-registration-contract.md)
- [02 — 构建 brightness semantic Adapter](issues/02-build-display-brightness-adapter.md)
- [03 — 增加本地 Assistant 入口](issues/03-add-local-assistant-entry.md)
- [04 — 执行 user-goal authorization](issues/04-enforce-user-goal-authorization.md)
- [05 — 验证 cancellation 与 result 语义](issues/05-verify-cancellation-and-result-semantics.md)
- [06 — 注册一个 Native App capability](issues/06-register-native-app-capability.md)
- [07 — 注册一个 Runtime App capability](issues/07-register-runtime-app-capability.md)
- [08 — 连接主要 voice Provider](issues/08-connect-a-voice-provider.md)

## Further Notes

架构见 [AI Native](../../docs/design/architecture/07-ai-native.md)，决策见 [ADR index](../../docs/adr/README.md)。

原 A0–A5 顺序保留为 ticket group：A0 = 01、A1 = 02、A2 = 03–05、A3 = 06、A4 = 07、A5 = 08。A1 → A2 是最小 mainline；A3–A5 在各自依赖可用时分支推进。
