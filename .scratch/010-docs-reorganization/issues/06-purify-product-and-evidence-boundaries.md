# 06 — 纯化产品文档与证据边界

**What to build:** 删除源码树中的原始验收产物和重复 verification 文档，并把产品设计改为编号化、可验证且包含 AI Native 要求的纯产品契约。

**Blocked by:** 05 — 整理文档语义与自动化。

**Status:** resolved

- [x] 28 个原始 evidence 文件中的关键事实已写入 Milestone records，raw files 从当前源码树删除。
- [x] 删除独立 verification 文档；每个阶段的步骤、门槛和判定只由自己的 acceptance 维护。
- [x] 产品文档按 `01–06` 编号，并使用稳定 Requirement ID 与统一结构。
- [x] AI Native 成为独立基础产品要求，同时进入每个产品领域的必填章节。
- [x] 产品文档不再引用 Milestone、决策记录、任务、源码或 evidence。
- [x] Checker 持续验证 product purity、编号、结构、Requirement ID，并阻止 raw evidence 目录回到源码树。

## Resolution

源码树只维护可阅读的权威语义和已提炼的验收事实，不长期保存原始构建或串口日志；产品目录直接表达可验证行为，并把 AI Native 纳入所有产品领域。

## 后续文档归属

2026-10-02：本票记录的阶段文档路径属于当时的迁移历史。当前状态、验收和 records 已由 [08](08-unify-task-acceptance-records.md) 统一到本地 tracker，现行规则见 [文档入口](../../../docs/README.md)。
