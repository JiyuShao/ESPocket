# 01 — 整理上游材料与兼容目录职责

**What to build:** 上游材料归属 .scratch records 与 compat/patches 职责说明，保留所有原有证据。

**Blocked by:** None.

**Status:** resolved

- [x] compat 与 patches 并列，说明各自内容和当前接入状态。
- [x] 全部日期上游核查和故障报告/提交草稿放入对应 .scratch records，移除 docs/upstream。
- [x] 迁移清单覆盖已有五份快照、两份报告和对应真实工作票。
- [x] 所有本地链接迁移，历史证据保留。
- [x] Markdown、host checks 与空白检查通过。

## Comments

2026-10-03：用户选择 compat 与 patches 分开，并指出 upstream 杂乱、issues 与 .scratch 类似。因此改用 reports 表达故障材料；本次不授权 Runtime 补丁正式接入。

2026-10-03（更正）：用户说明问题是是否推荐把故障材料放到 .scratch，而非改 issues 名称。按现有文档职责，两个故障报告归具体 Effort 的 records；不设独立 reports 目录。

2026-10-03（最终范围）：用户进一步选择全部 upstream 材料作为 .scratch 内容。五份核查与两份报告分配给其实际领域的 Effort records，不保留 docs/upstream 或另一份索引。

## Resolution

七份上游材料迁移到领域 Effort records，docs/upstream 移除，compat/patches 职责分开。原证据除相对链接外逐份一致；主机与文档检查通过。见[迁移证据](../records/2026-10-03-upstream-materials-migration.md)。
