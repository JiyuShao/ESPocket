# 01 — 复现 Platform Baseline

**What to build:** 一套不依赖 workspace 生成状态、能够产出 ESPocket firmware 的 clean ESP-IDF/Brookesia/board configuration。

**Blocked by:** None — 历史上的第一个 slice。

**Status:** retrospective-resolved

- [x] 记录准确的 platform 与 board identity。
- [x] Dependency 能从声明和 lock data 解析。
- [x] 删除生成目录后 clean build 完成。

## Resolution

根据已接受的 M1 build 与 environment table 重建；中间工作的准确顺序未知。
