# 04 — 验证文档系统

**What to build:** 一条命令检测 broken link/anchor、无效 evidence 引用、glossary drift、未分类工作与过期 architecture diagram。

**Blocked by:** 03 — 拆分设计、工作与历史。

**Status:** resolved

- [x] Checker 覆盖 Markdown link 与本地 anchor。
- [x] Checker 执行 Context 与 `.scratch` marker 规则。
- [x] Checker 验证生成 SVG identity 并执行 layout check。

## Resolution

已增加 `scripts/docs/check.py` 作为仓库级验证入口，并在 Agent 与文档指南中记录命令。
