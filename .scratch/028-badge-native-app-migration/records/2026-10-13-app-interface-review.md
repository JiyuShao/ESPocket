# 2026-10-13：App 接口与 IMU 提案审查

用户要求严肃 review 命名规范与接口设计。本轮只审查和记录结果，没有修改 firmware 实现、操作设备或生成新候选。

## 范围与证据

- 固定基线 `22bf91a2cda93903ebf527a0376d4d844182fee6`，比较 `git diff 22bf91a...366634d`；两次提交为 `a818955`（Native content）与 `366634d`（暂停/泡泡纸）。重点为新增 Core/GUI/Audio 公共接口及泡泡纸调用；锁定的原作源码/素材作为输入，不作为本轮新设计逐行审查。
- 实际补丁后源码核查目录 `/private/tmp/espocket-028-lifecycle-build-v5/patched_components`；checkout 与隔离工程的原始 managed_components 均未手改。
- 规范依据：CONTEXT、AGENTS、ADR-0003/0016、架构 LAY-001–006、开发契约。未发现独立 CODING_STANDARDS 或 CONTRIBUTING；PascalCase 类型、snake_case 方法总体符合现有惯例。以下命名建议属于语义设计判断，不包装成命名格式硬违规。
- 契约依据：[03](../issues/03-system-lifecycle-and-activity.md)、[04](../issues/04-imu-capability.md)、[10](../issues/10-native-content-and-pointer-seam.md)及 [App 契约](../../../docs/design/product/04-app-contract.md)。IMU 的 `acquire(options)`、`latest()`、`close()` 只是会话提案，尚未实现或定名。
- code-review 的 Standards 与 Spec 两条线独立审查，下列保持分开。优先级指本轮接口工作；提案风险与已复现故障分别标注。

## Standards

1. **P2，现有接口：活动资格与输入帧的关联交给调用方。** [Core 自绘补丁](../../../firmware/patches/espressif__brookesia_system_core/0.8.4/027-app-owned-native-content.patch)第 154–159 行获取准入 epoch，但返回帧不携带活动凭据；[泡泡纸调用](../../../firmware/native_apps/bubble_wrap/src/bubble_wrap_app.cpp)第 65–77 行分别获取 execution_state 和 pointer frame，再用两个裸 `uint64_t` 上报。建议准入 Owner 返回绑定输入的 `UserActivityToken`，`report_user_activity(token)`；非触摸输入也应在准入当时捕获资格，不能在发送迟到活动时换取新资格。当前泡泡纸先取资格再读帧，未由本轮证明会接受旧输入；这是降低调用方误用风险的接口优化。
2. **P3，现有命名：AppExecutionState/suspended 不能代表完整运行资格。** [028 补丁](../../../firmware/patches/espressif__brookesia_system_core/0.8.4/028-app-suspension-and-activity.patch)第 40–48 行只有原因/失败标志，没有真实 AppState 或前台事实；Starting、后台 Running 都可能 `suspended()==false`。建议快照投影已有 AppState/前台事实，暂停原因查询明确命名为 `has_suspension_reasons()`；身份用 `AppInstanceId`，字段用 `instance_id`，明确启动尝试时分配、成功后沿用。不得增加另一份生命周期缓存。
3. **P3，现有策略：boolean 使调用意图不明确。** 028 补丁第 75–80 行 `completion` 实际允许暂停期间分发；[Audio 补丁](../../../firmware/patches/espressif__brookesia_service_audio/0.8.2/001-select-idle-output-atomically.patch)第 8–9 行 `only_if_idle` 检查是否占有 active source，而非是否正在发声。建议命名 `TimerDispatchPolicy::{RunningOnly,AllowWhilePaused}`、`SourceSelectionPolicy::{Replace,IfUnoccupied}`，保留现有默认行为与系统 Owner 的使用范围。`set_app_suspension` 的连续 boolean 也可用含命名字段的事实结构减少参数顺序依赖。
4. **P2，IMU 提案：租约须由 Owner 强制撤销。** 04 要求暂停/失败清理，不能仅依靠 App 在回调中 close。建议不可复制、可移动的 `MotionSamplingLease`；正常显式关闭和析构兜底之外，Owner 使暂停/停止/失败的旧 lease 永久失效，恢复后申请新的 lease。实际 Core 与采样 Owner 的接入机制尚待设计，不能以 RAII 类型存在认定要求已满足。
5. **P2，IMU 提案：latest/acquire 尚缺可判定结果。** 建议 `read_latest_sample()`、`MotionSample`、类型化错误；明确通道、样本时间/序号、freshness、坐标系与实际采样率。多使用方的频率/通道合并需由同一采样 Owner 执行，例如采用有效需求中的最高频率，并明确硬件不支持时拒绝还是协商降级。板级轴向和屏幕旋转映射分别说明。玩法滤波仍在 App，不建立通用游戏框架。

## Spec

1. **P1，已复现代码故障：原因回调重入后仍恢复被覆盖 App。** 03 要求“全部原因解除且同实例仍有效、仍有前台资格时才恢复”。028 补丁第 241 行缓存 `pause`，第 320 行执行 `on_suspension_changed` 后，第 323–329 行仍用旧 pause 决定调用 on_resume，之后才检查最新 suspended。原因回调重入加入覆盖时，内层保持 Paused，外层却发 resume；App 重启的动画/worker/采样可能继续，而 Core 状态保持 Paused，也没有第二次 on_pause。

   用现有 [生产方法 host harness](../../../firmware/test/host/test_app_suspension.py)扩展临时断言复现，未改仓库测试：`result=error state=Paused covered=1 calls=pause,change,change,change,resume`。临时源码 `/private/tmp/espocket-review-reason-nested.cpp`；包装测试 exit 1，因“不应调用 resume”的断言失败。原测试只覆盖 resume 内新增覆盖，未覆盖 reason callback 内新增覆盖。修复应在任何恢复副作用前重新核验同实例、最新原因、前台及 lifecycle_failed；补回归确保没有多余 resume。此前 v5 候选包含此缺陷，不能作为修复后的候选复用；原离线通过记录继续是当时实际结果，本次补充其覆盖缺口。
2. **P1，IMU 实施前阻塞：实例授权与撤销接入未定。** 04 要求“暂停/停止/失败后无遗留采样或迟到回调”。现有 execution_state 通过持久 app_id 查询当前快照；旧回调重新读取可看到新实例，不能把当前快照作为旧任务换取新 lease 的授权证明。应在生命周期/请求准入入口固定身份，lease 绑定它，Core 在暂停/停止/失败时通知真实采样 Owner 撤销。App close/析构和 HAL InterfaceHandle 的 device lifetime 均不等价于此撤销机制。
3. **P2，IMU 设计待补：共享采样与释放失败结果未定。** 04 要求“单位、坐标轴、时间戳、有效性、采样与启停失败”及“错误与未就绪可区分”。需明确请求/实际频率、加速度和陀螺仪各自有效性及时间戳、新 lease 不读暂停前缓存、超龄阈值、revoked/not-ready/read-failed 的区别，以及最后一份 lease 关闭后硬件停止失败的报告/重试。类型化错误和 MotionSample 不能只换名字，必须带上述行为。关闭时先撤销交付资格；物理停止失败由 Owner 保留清理责任并可诊断，不能继续把旧样本交给 App。

## 后续

优先修复 Spec 1 并补生产回归，重建候选；03 重开，设备门槛仍由 09 持有。其余现有接口优化先确定兼容迁移范围，避免为了改名重写整个 AppContext。IMU 接口在实现 04 前补齐租约、共享采样与错误契约。Standards 5 项（最高 P2）；Spec 3 项（最高 P1，其中代码故障 1 项、提案未定 2 项）。
