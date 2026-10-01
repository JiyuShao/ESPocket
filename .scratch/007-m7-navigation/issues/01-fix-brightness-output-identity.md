# 01 — 修复 brightness output identity

**What to build:** Shell brightness 读写 System 选择的真实 Display output，不使用固定 `OutputId = 0`。

**Blocked by:** None；真实效果由 [03 导航真机验收](03-run-navigation-hardware-acceptance.md) 记录。

**Status:** resolved

- [x] System 与 Shell 共享同一 selected-output fact。
- [x] Brightness read/write 使用有效 output identity。
- [x] 现有 Settings brightness 行为保持完整。

## Resolution

2026-10-02：System 将真实选定的 Display output ID 传给 Circular Shell；Brightness Card 与 Quick Settings 的读写均使用该 ID。Settings App 路径未修改，主机构建通过。实际设备亮度变化留在 M7 hardware acceptance 验证，见[源码与构建记录](../records/2026-10-02-brightness-output-id.md)。
