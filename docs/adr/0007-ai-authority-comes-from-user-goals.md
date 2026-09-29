# ADR-0007: AI authority comes from confirmed user goals

- Status: `accepted`
- Recorded: 2026-09-29
- Origin: 从既有 AI Native 设计中提取；首次决策日期未知

## Context

App 或 Agent 可以请求 Action，却不一定代表用户意愿。把任意 prompt 或 capability 请求视为 authority，会允许权限提升和 confused-deputy 行为。

## Decision

AI authority 来源于已确认的 User Intent 或有效 Scoped Grant。只有产品 authorization、实际 caller、Action Risk、目标 Owner admission rule 与 Brookesia permission 的交集允许执行。高影响步骤需要单独确认。

## Consequences

- App 或 Agent 文本只是输入，不能证明用户 authorization。
- Grant 具有 capability、target、duration 与 caller 边界。
- Permission 在执行时重新评估。
- 提交后的不确定结果必须如实报告，不能盲目重试或假定已回滚。

## Alternatives rejected

- 将 App prompt 或 click 视为 User Intent。
- 允许 Assistant 代理技术上可到达的任意 capability。
- 用一次 approval 授权无关的未来操作。

参见 [AI Native 架构](../design/architecture/07-ai-native.md)。
