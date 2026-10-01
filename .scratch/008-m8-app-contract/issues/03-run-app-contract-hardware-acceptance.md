# 03 — 执行 M8 App contract hardware acceptance

**What to build:** 分别取得真机 evidence，证明 Native 与 Runtime App 满足 Page 导航、Root 无 Back、Home、wake、待决 Back 与 reclaim 行为。

**Blocked by:** M7 `PASS`；02 — 增加 App reclaim test seam。

**Status:** ready-for-human

- [ ] 四条固定 Native/Runtime path 各通过 5 次。
- [ ] 两种模型的 Screen Off/Wake、horizontal swipe、Root 无 Back 与待决 Back 检查通过。
- [ ] Lifecycle 与 heap evidence 无持续 regression。

## Comments

- 2026-10-01：原任务验证 Native 与 Runtime 的 `navigation、Home、wake、invalid-source 与 reclaim`，并检查 `horizontal swipe 与 invalid-source`。Root 无 Back 决策移除直接来源回退，改为验证 Page 栈与待决 Back；原验收意图保存在此。
