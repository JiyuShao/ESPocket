# 02 — 闭合 Home 与 cleanup loop

**What to build:** Home 在 Core task 中停止前台 Native App，恢复 Launcher，并释放 GUI 与 callback state。

**Blocked by:** 01 — 交付可见 Native App tracer bullet。

**Status:** retrospective-resolved

- [x] Display callback 发布 intent，不直接调用 Core。
- [x] System 只清理匹配的 foreground generation。
- [x] GUI unload 与 callback cleanup 可观察。

## Resolution

最终 Home concurrency 修复后已接受；更早 image 保持 superseded。
