# 01 — 修复 brightness output identity

**What to build:** Shell brightness 读写 System 选择的真实 Display output，不使用固定 `OutputId = 0`。

**Blocked by:** 实现无依赖；M6 `PASS` 是 M7 acceptance gate。

**Status:** ready-for-agent

- [ ] System 与 Shell 共享同一 selected-output fact。
- [ ] Brightness read/write 使用有效 output identity。
- [ ] 现有 Settings brightness 行为保持完整。
