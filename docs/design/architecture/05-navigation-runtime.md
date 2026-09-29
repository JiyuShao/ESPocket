# 05 — 导航与应用运行

## 目的

定义 Shell Surface、App 页面、Back、Home、Screen Off 与 Wake 的组合方式，并明确导航状态由哪个 Module 拥有。

## 支撑的产品要求

- [INT-001–INT-016](../product/03-interaction-model.md)
- [APP-001–APP-007、APP-010、APP-015](../product/04-app-contract.md)

## 结构

![ESPocket 顶层导航 Surface](assets/navigation-surfaces.svg)

![ESPocket 显示状态](assets/display-state.svg)

![ESPocket 应用运行模型](assets/app-runtime.svg)

## 架构不变量

| ID | Invariant |
|---|---|
| NAV-001 | Watch Face、Cards、Quick Settings 与 Launcher 是 Shell Surface；前台 App 由 System Core 管理。 |
| NAV-002 | CircularShell 解释手势和可见 Surface，`espocket::System` 记录一个直接 Launch Source。 |
| NAV-003 | App 的 Screen Flow 拥有 Root 与 Detail 内部导航；System Core 拥有 App 启停。 |
| NAV-004 | Root Back 停止 App 并恢复直接 Launch Source；来源失效时恢复 Watch Face。 |
| NAV-005 | PWR Home、Screen Off 与 Wake 由 `espocket::System` 编排，App 不得拦截。 |
| NAV-006 | Display State 与导航正交；息屏不执行 Back 或 Home。 |
| NAV-007 | Native 与 Runtime App 使用不同 Adapter 接入同一生命周期与导航 Seam。 |

## AI Native

Assistant 调用 Home、Back、打开 Surface 或读取 Display State 时，仍通过目标 Owner 和同一导航生命周期执行。需要显示 UI 的 Action 必须定义 Launch Source、PWR 行为和 Running Instance 失效规则。

Exposure Decision：开放稳定导航语义，不开放 GUI 自动点击、坐标、手势注入、LVGL 对象或绕过授权的 App prompt。

## Code Anchors

- [circular_shell.hpp](../../../firmware/components/shell_circular/include/espocket/circular_shell.hpp)
- [circular_shell.cpp](../../../firmware/components/shell_circular/src/circular_shell.cpp)
- [system.cpp](../../../firmware/components/espocket_system/src/system.cpp)

## 非目标

- 定义手势识别算法、动画实现或 UI Widget 层级。
- 建立任意长度的 App-to-App 返回历史。
- 为 Runtime App 建立独立导航系统。
