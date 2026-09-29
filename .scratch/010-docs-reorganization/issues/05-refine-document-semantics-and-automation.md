# 05 — 整理文档语义与自动化

**What to build:** 按真实责任拆分 evidence、verification 与 script，统一中文叙述，并自动维护 Sequence、可发现性与 CI validation。

**Blocked by:** 04 — 验证文档系统。

**Status:** resolved

- [x] 阶段专属 evidence 与 shared evidence 分开，迁移前后 raw file SHA-256 集合一致。
- [x] Hardware verification 归入 Milestone；firmware build guide 只保留构建语义。
- [x] 文档 script 按 docs/tracker 责任分组，并增加 Effort scaffolder。
- [x] `.scratch`、ADR 与 Agent 指南统一为中文叙述，精确标识保持 English。
- [x] Checker 覆盖 orphan Markdown、evidence 引用与重复 raw evidence，CI 执行同一入口。

## Resolution

文档体系现在按 authority 与生命周期归位；新增维护动作由 `scripts/docs/`、`scripts/tracker/` 和 Documentation workflow 提供可重复入口。

## Comments

后续检查发现，把共享 evidence 与独立 verification 放入 `docs/milestones/` 仍然混合了原始产物和权威文档。最终由 [06 — 纯化产品文档与证据边界](06-purify-product-and-evidence-boundaries.md)删除 raw evidence 与共享 verification；本 ticket 保留用于追溯调整顺序。
