# 03 — 执行 Native lifecycle 与 heap gate

**What to build:** 默认关闭的 stress path 与 verifier，证明 50 轮完整 Native lifecycle 没有持续 heap loss。

**Blocked by:** 02 — 闭合 Home 与 cleanup loop。

**Status:** retrospective-resolved

- [x] 50/50 轮都到达 Running 与 Stopped。
- [x] GUI negative probe 确认 unload。
- [x] 四项 heap loss metric 均不超过 1,024 bytes。

## Resolution

50/50 和四项 heap loss 为 0 的已接受结果见[历史报告](../records/2026-09-26-acceptance-report.md)。
