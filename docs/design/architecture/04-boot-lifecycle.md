# 04 — 启动与生命周期

## 目的

定义设备启动顺序、失败分类、App 生命周期和语义能力失效顺序，确保 Native 与 Runtime App 共用同一状态事实。

## 支撑的产品要求

- [OVR-002、OVR-003、OVR-011–OVR-015](../product/01-overview.md)
- [APP-004、APP-005、APP-006、APP-010、APP-011](../product/04-app-contract.md)
- [AIN-006、AIN-007、AIN-008](../product/02-ai-native.md)

## 结构

![ESPocket 启动生命周期](assets/boot-lifecycle.svg)

![ESPocket App 生命周期](assets/app-lifecycle.svg)

## 架构不变量

| ID | Invariant |
|---|---|
| LIF-001 | ServiceManager 与显示来源必须先于 System Core 和 App 启动。 |
| LIF-002 | Display、Touch、System Core 或 Shell 基础启动失败必须终止启动并返回错误。 |
| LIF-003 | Time、Wi-Fi 与 Battery 状态不可用不得阻止 Home 启动，Shell 使用明确降级状态。 |
| LIF-004 | Native 与 Runtime App 共用 System Core 的 App 状态机、前台跟踪和恢复 Hook。 |
| LIF-005 | App 停止必须先使外部访问失效，再释放实例拥有的 GUI、Timer、订阅和临时状态。 |
| LIF-006 | 被回收或失效的实例不得恢复旧页面；再次启动产生新的 Root 与实例 identity。 |
| LIF-007 | 同一 ESPocket System 对象必须支持正常 stop→start 与 deinit→init；重新运行重建所需 binding、请求关系和输入状态，不复用已失效的 App Running Instance。关键启动失败不承诺原地重试。 |
| LIF-008 | System stop 撤销产品执行入口并停止所有受管 App；deinit 进一步释放资源。Service 继续遵守真实 Owner 与 binding 生命周期，不通过复制生命周期状态达成停机。 |

## AI Native

App 只有进入 Running 后才能注册属于该实例的 Context、Action 和 Event。停止、崩溃、重启或回收先撤销可发现性和调用能力，再清理实例；重新启动产生新的注册 identity。跨 App 生命周期持续的能力由 Brookesia Service 拥有。

Exposure Decision：System、Shell 和 Service 可以注册与各自生命周期一致的能力；App 能力不得超出单次 Running Instance。

## Code Anchors

- [app_main.cpp](../../../firmware/main/app_main.cpp)
- [system.cpp](../../../firmware/components/espocket_system/src/system.cpp)
- [circular_shell.cpp](../../../firmware/components/shell_circular/src/circular_shell.cpp)
- [System Core app manager](../../../firmware/managed_components/espressif__brookesia_system_core/src/app/manager.cpp)

## 非目标

- 建立第二套 Native/Runtime 生命周期。
- 保证 App 后台驻留或恢复失效页面对象。
- 用诊断日志替代生命周期 Interface 的结果。

## PWR 输入与执行上下文

PowerKeyMonitor 只采样和暂存短按事件，System 消费并执行 Home、Screen Off 或 Wake。Circular Shell 不读取按键计数、不转发 PWR Home；其通用 ShellHost tick 提供维护节拍。同一处理周期中的 PWR 先于未提交的键盘或确认结果，已提交操作仍由真实 Owner 核实。App 启动等待不得阻塞 PWR Home 的产品响应目标。

停止时 System 先撤销产品执行入口并设置 stopping guard，停止按键采样，再停止 Shell 与全部受管 App，防止旧输入进入新运行；deinit 进一步释放资源。正常重复运行与关键失败后显式重启的保证分开。

## 可见 App 的分阶段启动

System 向 Core 请求可见 App 启动；Core 在原 AppRecord 持有 Starting、取消及回滚阶段，GUI 准备在真实 GUI task 中执行，App Owner 等待期间继续处理其他节拍。只有完成最终 hook 才提交成功，停止或失败不能复活取消的实例。System 不创建启动工作队列或镜像状态，仍使用 Core AppInfo 和完成 hooks。

启动阶段内的同步 callback 与 GUI parse 不提供强制抢占；分阶段只释放阶段之间与 GUI future 等待时的 App Owner。输入响应时延还取决于每个阶段的耗时与 GUI 锁占用。

Core 的公开同步启动与分阶段启动共用私有准入、Runtime 启动、生命周期调用、Running 提交和资源清理操作；两种入口仅保留各自调度及兼容语义。准入与生命周期失败由同一分类报告，不再各自维护错误提示。

## 暂停原因与活动准入

Core 在原 AppRecord 保存单次启动身份和覆盖/息屏/手动暂停原因；System 仅传入产品事实，不镜像 App 状态或管理另一套生命周期。首次暂停与末次恢复都由 Core 判定，失败保持暂停，旧身份或丢失前台资格拒绝恢复。前台恢复投影将同次 Paused 实例视为仍有效，不因此创建新实例。

普通 periodic timer 在 Paused 时跳过；一次性 due 在原 timer record 暂存，恢复后由既有维护节拍分发；停止清空。Owner completion pump 可显式保留暂停分发，服务事件与请求完成遵守原身份撤销。用户活动经 Core 实例与 Shell input epoch 重新准入后，写入 Shell 既有闲置代次，不能唤醒已息屏页面。公开接口与失败处理见 [App 暂停与活动](../../development/app-suspension-and-activity.md)。
