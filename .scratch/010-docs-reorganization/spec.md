# 文档重组

Sequence: 010

Status: resolved
Blocked by: None.

## Problem Statement

ESPocket 文档混合了 glossary、产品契约、架构理由、实施计划、状态与 raw evidence，导致人和 Agent 需要阅读重叠或过期来源。

## Solution

采用 Matt 风格的 glossary、ADR、本地 Spec 与 ticket 职责，同时保留长期产品设计、架构视图、Milestone acceptance、历史 records、upstream research 与操作指南。

## User Stories

1. 作为 maintainer，我希望每类含义只有一个权威来源。
2. 作为 Agent，我希望通过短入口找到任务所需的准确 context。
3. 作为 reviewer，我希望 rationale 与产品规则、实施计划分离。
4. 作为历史维护者，我希望旧结果与 evidence 保持可追溯。
5. 作为 contributor，我希望只有一条文档验证命令。

## Implementation Decisions

- 保留一个纯根 glossary 与全系统 ADR 目录。
- 在 `.scratch/` 下使用版本化本地 Markdown Spec，并让每个 ticket 独立成文件。
- 保留同时面向人和 Agent 的产品与架构文档。
- 当前状态只保存在 Milestone summary 与 acceptance 文件。
- 将 M1–M5 长报告移到 `records/`，并把影响判定的 raw evidence 提炼为长期事实。
- 融合 AI Native 产品与架构设计，消除独立语义孤岛。

## Testing Decisions

- 检查 relative link、anchor、evidence path 与 Context 结构。
- 重新生成 architecture SVG，并执行 layout collision 检查。
- 要求 `.scratch` 显式记录 status 与 retrospective marker。

## Out of Scope

修改 firmware 行为、改写已接受的历史事实，或宣称未验证的 Milestone 结果。

## Tickets

- [01 — 建立 Matt 仓库约定](issues/01-establish-matt-repository-conventions.md)
- [02 — 提取长期决策](issues/02-extract-durable-decisions.md)
- [03 — 拆分设计、工作与历史](issues/03-split-design-work-and-history.md)
- [04 — 验证文档系统](issues/04-validate-documentation-system.md)
- [05 — 整理文档语义与自动化](issues/05-refine-document-semantics-and-automation.md)
- [06 — 纯化产品文档与证据边界](issues/06-purify-product-and-evidence-boundaries.md)
- [07 — 收敛产品、架构与 Firmware 文档](issues/07-converge-product-architecture-and-firmware-docs.md)

## Further Notes

迁移路径与已完成 slice 记录在本目录的 resolved tickets 中。
