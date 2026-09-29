# ADR-0006: AI semantic access stays with real Owners

- Status: `accepted`
- Recorded: 2026-09-29
- Origin: 从既有 AI Native 设计中提取；首次决策日期未知

## Context

System、Shell、Service 与 App 已经持有产品状态、副作用和生命周期。把这些责任转移到全局 AI manager 会造成状态冲突和失败恢复冲突。

## Decision

AI Native 是覆盖既有 Owner 的语义访问维度。Context、Action 与 Event 在 Owner 边界注册，聚焦的 Adapter 将产品语义映射到 Brookesia 公开接口。AI Native 不增加第二套全局 manager、状态 registry、event bus 或生命周期系统。

产品 UI 与 Assistant 可以共用一个语义 Action 入口，但 authorization 必须针对实际 caller 评估。

## Consequences

- Owner 继续作为状态与副作用的来源。
- Assistant 不自动操作 GUI 控件，也不直接调用 HAL。
- 第一个 capability 使用聚焦 Adapter；通用抽象等待第二个真实 capability。
- Brookesia 版本细节封装在 Adapter 之后。

## Alternatives rejected

- 持有系统 capability 的全局 AI Manager。
- 重复状态或并行 Event Bus。
- Assistant 直接访问 Brookesia 内部实现或 HAL。

参见 [AI Native 架构](../design/architecture/07-ai-native.md)。
