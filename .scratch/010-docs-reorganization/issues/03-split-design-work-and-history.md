# 03 — 拆分设计、工作与历史

**What to build:** 产品契约、架构视图、Milestone acceptance、历史记录、upstream fact、guide 与本地工作各自拥有明确权威位置。

**Blocked by:** 02 — 提取长期决策。

**Status:** resolved

- [x] M1–M5 report 移入 `records/`，并增加简洁 acceptance summary。
- [x] M1–M8 Spec 与 ticket 明确区分 retrospective 与 current status。
- [x] AI Native 语义完成融合，实施计划移入 `.scratch/`。

## 旧路径映射

| 旧路径 | 新权威位置 |
|---|---|
| `docs/design/policies/package-trust.md` | `docs/design/product/05-runtime-package-trust.md` + ADR-0004 + M5 Spec |
| `docs/design/policies/launcher-sync.md` | `docs/design/product/06-application-discovery.md` + ADR-0005 + M5 Spec |
| `docs/design/architecture/07-ai-native-os.md` | `CONTEXT.md` + product docs + architecture views + ADR-0006..0009 |
| `docs/design/architecture/08-ai-native-integration.md` | `.scratch/009-ai-native-foundation/` + upstream local baseline |
| `docs/milestones/mN-acceptance.md` | `docs/milestones/mN/acceptance.md` and `records/` |
| hardware acceptance files | 各阶段 `acceptance.md` 的 Hardware Acceptance 章节 |

## Resolution

已将每类含义移动到 `docs/README.md` 定义的权威位置，M1–M5 report 保留在 `records/`，并在拆分 evidence 目录时保持所有 raw Milestone evidence 字节不变。
