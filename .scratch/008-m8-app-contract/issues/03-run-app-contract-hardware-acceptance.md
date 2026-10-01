# 03 — 完成 App 交互真机验收

**What to build:** 分别取得真机 evidence，证明 Native 与 Runtime App 满足 Page 导航、Root 无 Back、Home、wake、待决 Back 与 reclaim 行为。

**Blocked by:** [007/03 系统导航真机验收](../../007-m7-navigation/issues/03-run-navigation-hardware-acceptance.md)；[014/04 Native/Runtime 导航绑定](../../014-app-navigation-card-contract/issues/04-samples-api-finalization.md)；[02 回收测试入口](02-add-app-reclaim-test-seams.md)；[003/02 Runtime lifecycle 与共存](../../003-m3-runtime-app/issues/02-prove-runtime-lifecycle-coexistence.md)（已完成）。

**Status:** ready-for-human

- [ ] 四条固定 Native/Runtime path 各通过 5 次。
- [ ] 两种模型的 Screen Off/Wake、horizontal swipe、Root 无 Back 与待决 Back 检查通过。
- [ ] Lifecycle 与 heap evidence 无持续 regression。

## Comments

- 2026-10-01：原任务验证 Native 与 Runtime 的 `navigation、Home、wake、invalid-source 与 reclaim`，并检查 `horizontal swipe 与 invalid-source`。Root 无 Back 决策移除直接来源回退，改为验证 Page 栈与待决 Back；原验收意图保存在此。

## 真机步骤与逐项结果

本票要求 Native 与 Runtime 分别提供真机证据。Runtime lifecycle 基线已通过，但不能替代本票的真实 Runtime 导航、恢复与回收验证。

### Fixed repetition counts

以下次数均为固定验收要求，且不超过 5 次。任何一次失败都必须记录，不能追加次数稀释失败。

| 执行模型 / 路径 | 次数 | PASS 条件 | 状态 |
|---|---:|---|---|
| Native Root → Detail → Back → Root → PWR Home | 5 | 子页面 Back、Root 无 Back 与 PWR Home 均正确 | NOT TESTED |
| Runtime Root → Detail → Back → Root → PWR Home | 5 | 子页面 Back、Root 无 Back 与 PWR Home 均正确 | NOT TESTED |
| Native background reclaim → relaunch | 5 | 从 App Root 启动，不恢复失效页面 | NOT TESTED |
| Runtime background reclaim → relaunch | 5 | 从 App Root 启动，不恢复失效页面 | NOT TESTED |

### Required one-pass checks

| 检查项 | PASS 条件 | 状态 |
|---|---|---|
| Native App Screen Off / Wake | 未回收时恢复页面；回收时降级 Watch Face | NOT TESTED |
| Runtime App Screen Off / Wake | 未回收时恢复页面；回收时降级 Watch Face | NOT TESTED |
| Native normal horizontal swipe | 不误触发 Edge Back | NOT TESTED |
| Runtime normal horizontal swipe | 不误触发 Edge Back | NOT TESTED |
| Root Back attempt | 两种执行模型都保持 Root 且无默认 Back | NOT TESTED |
| Deferred Back | 重复请求不重复提交；超时取消；PWR 可立即回表盘 | NOT TESTED |
| Failure scan | 无 panic、watchdog、assert、deadlock、错误 Back 或持续性资源下降 | NOT TESTED |

## 证据规则

- 每次固定循环必须标识执行模型、attempt 编号、Page ID 与最终目标。
- Runtime 路径必须使用真实 Runtime App，不能用 Native mock 替代。
- Preview、host 测试或串口状态打印不能替代物理显示、触摸和 PWR 观察。
- Runtime 路径未通过或任一必需项缺少证据时，不得关闭本票。

## Lifecycle 与 heap 证据

- 复用项目现有 lifecycle 与 heap 证据格式。
- 回收可以通过明确、默认关闭的测试入口模拟，不要求实现完整低内存调度器。
- 每次回收必须证明旧页面和瞬时 Overlay 不再可恢复。
- 重新启动必须证明从 App Root 开始。
- Native 与 Runtime 的失败必须分别记录，不能互相替代。
