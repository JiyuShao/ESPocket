# 07 — 收敛产品、架构与 Firmware 文档

**What to build:** 取消空泛的 Guides 类别，统一 Product 与 Architecture 的长期文档格式，并让架构显式映射 Product Requirement、AI Native Exposure Decision 与 Code Anchors。

**Blocked by:** 06 — 纯化产品文档与证据边界。

**Status:** resolved

- [x] 构建说明迁到 `firmware/README.md`，删除 `docs/guides/`。
- [x] Product headings 统一为中文，AI Native 主文档不再重复嵌套同名章节。
- [x] 产品总览只保留跨领域原则，领域行为由后续 Product Requirements 唯一维护。
- [x] Architecture 使用编号标题、Product Requirement 映射、稳定 Invariant ID、AI Native 与 Code Anchors。
- [x] Architecture 不再维护实现进度、阻塞、日期、Spec 或 Milestone 引用。
- [x] Checker 验证 Product 与 Architecture 的结构、编号、ID、纯度和 Code Anchor。

## Resolution

长期文档现在围绕 Product Requirement 与 Architecture Invariant 组织；Firmware 操作知识回到代码目录，状态与可执行工作继续由 Milestone 和 `.scratch` 维护。

## 后续文档归属

2026-10-02：本票记录的阶段文档路径属于当时的迁移历史。当前状态、验收和 records 已由 [08](08-unify-task-acceptance-records.md) 统一到本地 tracker，现行规则见 [文档入口](../../../docs/README.md)。
