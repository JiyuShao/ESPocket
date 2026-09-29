# ADR-0009: AI Native is a foundational design dimension

- Status: `accepted`
- Recorded: 2026-09-29
- Origin: 项目所有者于 2026-09-29 明确确认

## Context

在 subsystem 完成后才补 AI access，通常会先暴露 UI mechanics 或低层 API，再回填 authorization 与 lifecycle 规则。这会产生不一致语义，并让 AI 变成并行集成层。

## Decision

每个新增或变更的产品 capability 与系统设计，都必须在设计人类交互和所有权时，同时作出明确的 AI Native Exposure Decision。该决定记录 Owner、可能的 Context/Action/Event 语义、authorization、Action Risk 和 lifecycle。

有效结果包括：注册稳定的 semantic capability；说明理由并保持 unexposed；或创建 ticket 延后处理。内部模块不必暴露 AI capability，原始 framework 或 hardware API 也不构成 Semantic Registration。

## Consequences

- Design review 将 Exposure Decision 视为完整性的一部分。
- Registration 发生在产品语义 Owner 边界。
- Human UI 与 Assistant path 可以汇聚到同一 Action，同时分别持有 authority。
- 延后项必须在 `.scratch/` 中保持可见。

## Alternatives rejected

- 先完成传统 subsystem，再补 AI Adapter。
- 要求暴露每个内部 class 或 method。
- 因为存在 framework API，就允许 AI integration 绕过产品语义。

参见[产品总览](../design/product/01-overview.md)和 [AI Native 架构](../design/architecture/07-ai-native.md)。
