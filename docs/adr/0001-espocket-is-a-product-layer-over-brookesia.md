# ADR-0001: ESPocket is a product layer over Brookesia

- Status: `accepted`
- Recorded: 2026-09-29
- Origin: 从既有设计中提取；首次决策日期未知

## Context

Brookesia 已经持有 App、Runtime、GUI、Timer、Package、Service 和 HAL 基础设施。在 ESPocket 中重建这些能力会拆分状态与生命周期所有权，并增加上游升级成本。

## Decision

ESPocket 通过 Brookesia 的公开 seam 组合产品行为，不 fork Core，也不创建产品自有的 framework manager、包格式、Installer 或设备抽象替代品。

Circular Shell 使用隐藏的 Native `IApp` 作为 Brookesia carrier，同时在产品模型中保持 system Shell 身份。只有第二个真实实现证明 seam 后，ESPocket 才增加 Shell 抽象。

## Consequences

- 产品策略位于 `espocket::System`、Shell 和聚焦的 Adapter 中。
- Framework 缺口可以阻塞产品工作，不能通过第二套 framework 绕过。
- Managed components 继续由上游持有；兼容代码必须显式且可移除。

## Alternatives rejected

- Fork Brookesia，或把 managed components patch 作为产品基线。
- 将 framework manager 复制进 ESPocket。
- 在第二个实现出现前构建私有 Installer、Runtime 或 Shell framework。

参见[产品总览](../design/product/01-overview.md)和[分层架构](../design/architecture/02-layered-architecture.md)。

## 限定修订

[ADR-0015](0015-runtime-async-stack-patch-exception.md) 仅允许 Runtime JS 0.8.3 异步栈配置补丁，经独立副本与明确回归门槛维护；其余边界保持不变。

补丁授权范围于 2026-10-03 被 [ADR-0016](0016-maintained-upstream-fixes.md) 更新；本记录保留原始决定。
