# 03 — 核心 Module 协作

## 目的

定义运行时深 Module 的 Interface、所有权和协作方式，使复杂度集中在少量高 Leverage Seam，而不是散落到入口、Shell 和各 App。

## 支撑的产品要求

- [OVR-001、OVR-002、OVR-003](../product/01-overview.md)
- [APP-003、APP-005、APP-006、APP-010](../product/04-app-contract.md)
- [AIN-008、AIN-011、AIN-013](../product/02-ai-native.md)

## 结构

![ESPocket 核心 Module 协作](assets/core-modules.svg)

### `espocket::System`

它的 Interface 保持为系统初始化、启动、停止和少量产品操作；Implementation 集中处理 Service 与显示装配、App 安装、前台跟踪、App 导航、Home、PWR 和显示恢复。删除该 Module 会让这些规则重新散落到入口、Shell 和 App，因此它承担真实 Depth。

### `CircularShell`

它通过 `IApp` 生命周期、Surface 操作、状态输入和键盘请求提供小 Interface，隐藏 JSON UI、Screen Flow、手势仲裁、Overlay 与圆屏布局 Implementation。

### `System Core`

它通过公开 Interface 隐藏 App Manager、Runtime Manager、GUI Runtime、Timer 和 Package Manager。调用者和测试应跨同一个 Seam 验证生命周期行为。

## 架构不变量

| ID | Invariant |
|---|---|
| MOD-001 | `app_main` 只创建并驱动 `espocket::System`，不承载产品策略。 |
| MOD-002 | `espocket::System` 是产品 Composition Root 和跨 Module 策略 Owner。 |
| MOD-003 | CircularShell 拥有可见 Surface 与输入解释，不拥有 App 安装或 Runtime 生命周期。 |
| MOD-004 | System Core 是 App 状态、运行期 identity、GUI 与 Runtime 生命周期的事实来源。 |
| MOD-005 | Brookesia ServiceManager 拥有跨 App 持续的设备和业务能力。 |
| MOD-006 | 测试通过公开 Interface 观察结果，不穿透 Module 验证私有 Implementation。 |

## AI Native

| Owner | 可注册语义 | 生命周期 |
|---|---|---|
| `espocket::System` | 跨 Module 系统 Context 与 Action | System 生命周期 |
| CircularShell | Surface、导航与可见产品状态 | Shell 生命周期 |
| Brookesia Service | 跨 App 持续设备或业务能力 | 有效 binding 与 Service 生命周期 |
| Native / Runtime App | App 自有 Context、Action 与 Event | 单次 Running Instance |

Exposure Decision：Assistant 只消费这些注册关系，不接管 Module 状态，也不通过新的全局 AI Manager 转发所有调用。

## Code Anchors

- [system.hpp](../../../firmware/components/espocket_system/include/espocket/system.hpp)
- [system.cpp](../../../firmware/components/espocket_system/src/system.cpp)
- [circular_shell.hpp](../../../firmware/components/shell_circular/include/espocket/circular_shell.hpp)
- [circular_shell.cpp](../../../firmware/components/shell_circular/src/circular_shell.cpp)

## 非目标

- 把入口函数、Shell 或 Assistant 变成全局 God Module。
- 为测试公开私有状态或复制一套浅层 pass-through Interface。
- 在产品层重新实现 System Core 或 ServiceManager。
