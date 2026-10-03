# 03 — 完成 App 交互真机验收

**What to build:** 分别取得真机 evidence，证明 Native 与 Runtime App 满足 Page 导航、Root 无 Back、Home、wake、待决 Back 与 reclaim 行为。

**Blocked by:** 剩余物理/视觉确认；[04 Runtime 异步栈修复](04-resolve-runtime-async-stack-overflow.md)的源码与自动门槛已通过； [007/03 系统导航真机验收](../../007-m7-navigation/issues/03-run-navigation-hardware-acceptance.md)；[014/04 Native/Runtime 导航绑定](../../014-app-navigation-card-contract/issues/04-samples-api-finalization.md)；[02 回收测试入口](02-add-app-reclaim-test-seams.md)；[003/02 Runtime lifecycle 与共存](../../003-m3-runtime-app/issues/02-prove-runtime-lifecycle-coexistence.md)（已完成）。

**Status:** ready-for-human

- [ ] 四条 Native/Runtime path 各完成一次集中验收。
- [ ] 两种模型的 Screen Off/Wake、horizontal swipe、Root 无 Back 与待决 Back 检查通过。
- [x] Lifecycle 与 heap evidence 无持续 regression（当前有限工作负载的有效 checkpoint；采样缺项与范围见记录，不作为长期稳定性证明）。

## Comments

- 2026-10-01：原任务验证 Native 与 Runtime 的 `navigation、Home、wake、invalid-source 与 reclaim`，并检查 `horizontal swipe 与 invalid-source`。Root 无 Back 决策移除直接来源回退，改为验证 Page 栈与待决 Back；原验收意图保存在此。

## 真机步骤与逐项结果

本票要求 Native 与 Runtime 分别提供真机证据。Runtime lifecycle 基线已通过，但不能替代本票的真实 Runtime 导航、恢复与回收验证。

### 单次路径

按用户已明确要求减少验证次数，每条路径集中执行一次；失败保留独立 attempt，修复后再执行，不以追加成功次数稀释失败。既有已接受结果继续有效。

| 执行模型 / 路径 | 次数 | PASS 条件 | 状态 |
|---|---:|---|---|
| Native Root → Detail → Back → Root → PWR Home | 1 | 子页面 Back、Root 无 Back 与 PWR Home 均正确 | PASS（复用[已接受物理结果](../../014-app-navigation-card-contract/records/2026-10-02-default-back-prototype.md)，本次合成复核通过） |
| Runtime Root → Detail → Back → Root → PWR Home | 1 | 子页面 Back、Root 无 Back 与 PWR Home 均正确 | PASS（普通修复镜像合成 PASS，2026-10-03 用户物理确认） |
| Native background reclaim → relaunch | 1 | 从 App Root 启动，不恢复失效页面 | PARTIAL（Native-only 合成 PASS，物理待检） |
| Runtime background reclaim → relaunch | 1 | 从 App Root 启动，不恢复失效页面 | PARTIAL（Runtime-only 合成 PASS，物理待检） |

### Required one-pass checks

| 检查项 | PASS 条件 | 状态 |
|---|---|---|
| Native App Screen Off / Wake | 未回收时恢复页面；回收时降级 Watch Face | PARTIAL（未回收物理结果已接受；当前合成通过，回收待检） |
| Runtime App Screen Off / Wake | 未回收时恢复页面；回收时降级 Watch Face | PARTIAL（当前未回收合成及用户物理确认 PASS，回收物理待检） |
| Native normal horizontal swipe | 不误触发 Edge Back | PASS（007/03 当前物理确认与本次合成复核） |
| Runtime normal horizontal swipe | 不误触发 Edge Back | PASS（本次合成通过，2026-10-03 Runtime 用户物理确认） |
| Root Back attempt | 两种执行模型都保持 Root 且无默认 Back | PASS（两种模型合成 PASS，Native 已接受、Runtime 本次物理确认） |
| Deferred Back | 重复请求不重复提交；超时取消；PWR 可立即回表盘 | PARTIAL（修复后两种模型合成 PASS，物理待检；原 Runtime 栈溢出 FAIL 保留于[记录](../records/2026-10-02-app-device-frontier.md)） |
| Failure scan | 无 panic、watchdog、assert、deadlock、错误 Back 或持续性资源下降 | PARTIAL（当前自动套件无 panic，独立回收 PASS，有限 heap/stack 已记录；物理待检，原栈溢出 FAIL 保留） |

## 证据规则

- 每条验收路径必须标识执行模型、attempt 编号、Page ID 与最终目标。
- Runtime 路径必须使用真实 Runtime App，不能用 Native mock 替代。
- Preview、host 测试或串口状态打印不能替代物理显示、触摸和 PWR 观察。
- Runtime 路径未通过或任一必需项缺少证据时，不得关闭本票。

## Lifecycle 与 heap 证据

- 复用项目现有 lifecycle 与 heap 证据格式。
- 回收可以通过明确、默认关闭的测试入口模拟，不要求实现完整低内存调度器。
- 每次回收必须证明旧页面和瞬时 Overlay 不再可恢复。
- 重新启动必须证明从 App Root 开始。
- Native 与 Runtime 的失败必须分别记录，不能互相替代。

- 2026-10-02：落实用户“验证次数改小、不要反复操作”的授权，四条路径各一次；物理/视觉条件与失败记录不变。新增回收开关与镜像准备见 02，本票仍需真实设备证据。

- 2026-10-02：007 前置已完成。当前 apps attempt 的 Native 合成路径通过、Runtime 在确认开关处栈溢出；自动通过不替代物理条件，失败不稀释。04 未解决前暂停回收验收，见[设备记录](../records/2026-10-02-app-device-frontier.md)。

2026-10-03：普通 c8d56e5e2 的完整 apps 合成套件通过，包含此前崩溃的 Runtime confirmation 与全部待决 Back 分支，见[补丁设备验证](../records/2026-10-03-runtime-stack-patch-validation.md)。上表的旧 FAIL 保留为历史；当前自动分支 PASS，Runtime 物理及回收/资源仍待检，不关闭本票。

2026-10-03：两种独立 reclaim 的 17 步设备路径各 PASS，包含另一模型不被回收和旧确认状态清理；有限资源数据未持续下降，栈余量最小 7400 bytes，缺失日志与测量范围明确保留。三条缺失物理路径见[晨间最小清单](../records/2026-10-03-overnight-frontier.md)，不重做已接受 Native 常规路径。

2026-10-03：用户要求先验收。当前无测试音 Audio 修正镜像 `b9b4a413f` 的完整 apps 57 步再次 PASS，release 与最终 Home 正常；一次 Runtime 物理检查待回应，见[当前固件验收](../records/2026-10-03-current-firmware-acceptance.md)。未关闭剩余物理条件。

2026-10-03：用户对当前镜像 Runtime 一次集中物理路径回复“全部正常”，对应画面/触摸/PWR 条件通过；专用 Native/Runtime 回收物理检查仍独立待完成，详见当前固件验收记录。
