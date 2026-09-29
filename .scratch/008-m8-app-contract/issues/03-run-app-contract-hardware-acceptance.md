# 03 — 执行 M8 App contract hardware acceptance

**What to build:** 分别取得真机 evidence，证明 Native 与 Runtime App 满足 navigation、Home、wake、invalid-source 与 reclaim 行为。

**Blocked by:** M7 `PASS`；02 — 增加 App reclaim test seam。

**Status:** ready-for-human

- [ ] 四条固定 Native/Runtime path 各通过 5 次。
- [ ] 两种模型的 Screen Off/Wake、horizontal swipe 与 invalid-source 检查通过。
- [ ] Lifecycle 与 heap evidence 无持续 regression。
