# App 暂停与用户活动

普通前台 Native/Runtime App 共用真实 Core AppRecord 的状态与暂停原因。ESPocket System 提交 Quick Settings 覆盖与屏幕电源事实；Core 决定首次暂停、末次恢复及失败结果。Shell、Card 和持续 Service 沿各自生命周期执行。实现验收归 [028/03](../../.scratch/028-badge-native-app-migration/issues/03-system-lifecycle-and-activity.md)。

## App 接口

生命周期命名按职责区分，Native 和 Runtime 保持同一产品语义：

| 职责 | 命名 | 含义 |
|---|---|---|
| 请求 Core 执行操作 | `start_app`、`stop_app`、`pause_app`、`resume_app` | Core 决定状态转移与调用顺序 |
| App 执行生命周期工作 | `on_start`、`on_stop`、`on_pause`、`on_resume` | 初始化、清理、停止或恢复本 App 工作；可以返回失败 |
| 已发生事实的系统通知 | `on_app_started`、`on_app_stopped` | 既有 System hooks；不替代 App 初始化和清理 |
| 暂停原因变化通知 | `on_pause_reasons_changed` | 交付命名字段快照；已经暂停时仍可通知 |

`on_start` 成功只表示这一启动 hook 完成，Core 仍负责完整启动结果。`on_stop` 是停止过程中的清理 hook，不能理解为资源已经释放后的通知。Core 在调用 `on_pause` 前撤销 Running/输入资格；`on_resume` 前重新核验实例、前台、失败状态及最新原因，成功后再次核验才提交 Running。回调内重入改变原因或实例时，外层不能使用旧快照继续恢复。恢复回调失败时，App 应清理部分恢复的工作，不能依靠未来的一次 on_pause。

Native App 通过 `AppContext::system_service().execution_state()` 读取本 App 的公开事实：本次启动 `instance`、`covered`、`screen_off`、`manual_pause`、`lifecycle_failed` 和可选 `activity_epoch`。安装身份与持久 AppContext 不代表运行身份。新启动分配新 instance；停止/失败状态返回空，Starting 可读取身份但无活动资格。

第一次进入暂停时，Core 先撤销 Running/输入资格，再调用 `on_pause`。每个原因变化另调用 `on_pause_reasons_changed`，包含已因覆盖暂停后又息屏的情况。Native 接口为 `on_pause_reasons_changed(AppContext &, const AppPauseReasons &)`；快照的 `covered`、`screen_off`、`manual_pause` 均为 boolean，在交付时从真实 AppRecord 读取。它描述原因，不授予运行资格；回调内重入可能使它过时，不应保存作为未来采样或活动的授权。

Runtime 接口为 `on_pause_reasons_changed(snapshot_json)`。锁定的 NativeValue 桥只支持基本值，Core 使用一个 JSON 字符串传同样三个命名字段，App 使用 `JSON.parse`；本次未扩大 Runtime 桥或增加另一份状态缓存：

```js
brookesia_app.on_pause_reasons_changed = function (snapshot_json) {
    const reasons = JSON.parse(snapshot_json);
    // 即使已因覆盖暂停，随后息屏也会交付 screen_off=true。
    // 这里按原因执行 App 的资源策略；不能同步等待主机或采样线程。
    return true;
};
```

旧 `on_suspension_changed` 保留为兼容入口：Native 的新 hook 默认转发旧 hook；覆盖新 hook 的 App 不再由 Core 重复调用旧 hook。Runtime 优先新 hook，只有 backend 明确报告该函数不存在时，才回退旧 `on_suspension_changed(covered, screenOff, manualPause)` 三个 boolean；两者均缺少仍可运行。新 hook 返回 false 或报告错误不会回退并掩盖失败。已有四个生命周期 hook 名称与参数不变。

所有原因解除、同一实例仍有效且仍占前台，才调用 `on_resume`。重复事实不重复 callback。公开手动 pause/resume 只改变 manual_pause，不解除系统原因、不重启停止的实例，也不把后台 App 提为前台。停止、重启、替换或 System stop 后的旧请求不能恢复任何 App。

App 必须暂停实际更新来源、动画、worker 和采样；Core 无法冻结任意 App 线程。恢复重置计时基准，丢弃暂停期间的触摸/传感器积累。连接回调提交非阻塞请求，不能同步等待对端。遥控覆盖时保留连接；息屏即使发生于已暂停状态也应释放按键并断开。

callback 返回错误或抛异常后 Core 保持 Paused，记录 last_error/lifecycle_failed，禁止继续恢复；Home 仍能停止它，重新打开产生新实例。App 可查询最新原因，但失败实例不承诺进一步 callback；因此失败路径必须自行清理或交给真实资源 Owner，不得依靠一次未来 resume 修复资源。

## Timer 与异步完成

暂停抑制普通 periodic timer，不补发暂停期间周期。到期的一次性 timer 保留一个 deferred 标记，恢复后的既有 Core maintenance tick 分发一次；显式取消或停止清除它。App 不应使用周期 timer 承诺后台业务。

`System::timer_start_periodic(..., completion=true)` 为系统 Owner 的完成泵保留暂停分发；当前 Runtime 导航 Promise 完成泵使用它。App 普通 timer 默认 false。GUI action 仅向 Running 分发；已有 Owner `on_event` 继续向 Running/Paused 分发，使网络返回、键盘/Dialog 结果和清理能完成。它们仍受原请求身份、取消与停止撤销规则约束，不授权被遮挡页面接收触摸。

## 用户活动

Native 输入准入时捕获 `instance` 与当时非空的 `activity_epoch`。有效移动、点击或滚动后调用 `report_user_activity(instance, epoch)`；函数返回是否接受。Core 重新核对运行身份、Running/前台、暂停原因及 Shell 当前输入 epoch，System 再沿 Shell 既有 activity_generation 更新闲置时间。迟到活动不得改为读取一个新 epoch 再补报。

旧实例、覆盖、息屏、模态输入或已消费手势的活动被拒绝，不唤醒屏幕。动画不是用户活动。主动息屏立即撤销资格；App 不创建自己的息屏计时器。受控触摸帧的取消/全松开规则见 [Native 自绘接口](native-content-api.md)。Runtime 首版通过上述暂停事实保持兼容，本次未新增非触摸活动 JS API。

## 证据边界

Host 执行实际 Core 生命周期、System 事实接入、timer 分发及 App 代码；GUI、设备和 Audio 边界使用替身。隔离候选与源码/hash 记录在 [028 工作记录](../../.scratch/028-badge-native-app-migration/spec.md)。真实无线、息屏/唤醒时序、触摸与声音仍由 [028/09](../../.scratch/028-badge-native-app-migration/issues/09-device-acceptance.md)验收。
