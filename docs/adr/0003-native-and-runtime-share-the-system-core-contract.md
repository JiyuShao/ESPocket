# ADR-0003: Native and Runtime Apps share the System Core contract

- Status: `accepted`
- Recorded: 2026-09-29
- Origin: 从既有设计中提取；首次决策日期未知

## Context

Native App 与 Runtime App 使用不同的加载 Adapter，但用户不应因为实现细节而得到不同的导航、显示或生命周期行为。

## Decision

两种执行模型都使用 System Core App 状态机，并共享 Root、Detail、Back、Home、Screen Off、wake、reclaim 以及 GUI/keyboard 所有权的产品契约。Runtime 特有的加载逻辑保留在 Brookesia backend 之后。

## Consequences

- 产品代码只维护一套前台与恢复模型。
- Native 与 Runtime 验收使用相同的行为词汇，同时分别保留证据。
- Runtime 集成不得引入第二套产品导航或 lifecycle manager。

## Alternatives rejected

- Runtime 专用的产品生命周期。
- 为 packaged App 定义不同的导航与恢复语义。

参见 [App 契约](../design/product/04-app-contract.md)和 [App 生命周期架构](../design/architecture/04-boot-lifecycle.md)。
