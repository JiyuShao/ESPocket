# 04 — 启动与生命周期

## 目的

定义设备启动顺序、失败分类、App 生命周期和语义能力失效顺序，确保 Native 与 Runtime App 共用同一状态事实。

## 支撑的产品要求

- [OVR-002、OVR-003](../product/01-overview.md)
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

PowerKeyMonitor 只采样和暂存短按事件，System 在既有 App callback task 上直接消费，并执行 Home、Screen Off 或 Wake。Circular Shell 不读取按键计数、不转发 PWR Home；其通用 ShellHost tick 只提供维护节拍，键盘完成与输入处理顺序保持一致。停止时 System 先设置 stopping guard、停止 monitor，再停止 Shell 和前台 App，防止旧输入进入新任务。
