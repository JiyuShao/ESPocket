# 01 — 构建并 stage Hello Runtime

**What to build:** 使用锁定 Toolkit 构建的最小官方 JavaScript Runtime package，并通过 System Core helper stage 到 LittleFS。

**Blocked by:** [002/03 Native lifecycle 与 heap](../../002-m2-native-app/issues/03-run-lifecycle-heap-gate.md)（已完成）。

**Status:** retrospective-resolved

- [x] Runtime JS 与 QuickJS 版本已锁定并完成链接。
- [x] Toolkit doctor/build 与 package integrity check 通过。
- [x] Staged tree 与 LittleFS image 包含预期 package。

## Resolution

M3 build、Toolkit 与 staging evidence 已接受；debug package 有意保持 unsigned。
