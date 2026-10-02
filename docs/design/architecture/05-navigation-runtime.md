# 05 — 导航与应用运行

## 目的

定义 Home Space、App Page 栈、Back、Home、Screen Off 与 Wake 的所有权，使 Native 与 Runtime App 获得相同的开发契约。

## 支撑的产品要求

- [INT-001–INT-004、INT-006–INT-008、INT-017–INT-020、INT-022–INT-025](../product/03-interaction-model.md)
- [APP-003–APP-006、APP-010、APP-016–APP-017、APP-019–APP-029](../product/04-app-contract.md)

## 结构

![ESPocket 顶层导航 Surface](assets/navigation-surfaces.svg)

![ESPocket 显示状态](assets/display-state.svg)

![ESPocket 应用运行模型](assets/app-runtime.svg)

ESPocket 的导航接口包含声明、转移和观察三部分：App 安装时声明唯一 Root、所有稳定 Page 类型 ID、可选 Card ID 与 Card 目标 Page；App 运行时调用 `push`、`pop`、`replace`、`resetToRoot`；ESPocket 从同一导航栈计算可见 Back、Edge Back 和只读页面快照。接口语义相同，Native 与 Runtime 通过各自 Adapter 接入。具体语言绑定与字段以开发协议为准。

## 架构不变量

| ID | Invariant |
|---|---|
| NAV-001 | Watch Face、Cards、Quick Settings 与 Launcher 是 Shell Surface；前台完整 App 由 System Core 管理。 |
| NAV-005 | PWR Home、Screen Off 与 Wake 由 `espocket::System` 编排，App 不得拦截。 |
| NAV-006 | Display State 与导航正交；息屏不执行 Back 或 Home。 |
| NAV-007 | Native 与 Runtime App 使用不同 Adapter 接入同一生命周期与导航 Seam。 |
| NAV-008 | CircularShell 拥有 Home Space Surface、Card 位置与横滑；完整 App 的普通触控归 App。 |
| NAV-009 | 普通 App 决定 Page 转移，ESPocket 拥有唯一 App Page 栈和当前 Page 快照；官方 Settings 的明确适配例外从其真实 Screen Flow 提供快照，Back 委托官方 App，禁止复制第二份栈。 |
| NAV-010 | App Root 是栈底，不提供可见默认 Back 或 Edge Back；子页面的 Back 请求通过统一分发入口到达 App 和导航栈。 |
| NAV-011 | App 可以暂缓、允许或取消普通 Back；一个导航任务最多有一个待决 Back，请求超时取消并报告错误。PWR Home、App 停止或崩溃使待决 token 失效。 |
| NAV-012 | App 可接管默认可见 Back 与 Edge Back，自行决定返回 UI 与手势，也可不显示按钮；自定义入口必须调用同一 Back 请求入口。使用 ESPocket 标准 Back 控件的页面不再叠加 Overlay Back。 |
| NAV-013 | Card 目标 Page 由 App 声明；ESPocket 校验目标，构造以 Root 为底的导航任务。目标失效降级到 Root 并记录错误。 |
| NAV-014 | PWR Home 清除当前 App 导航任务并显示 Watch Face；下次启动从 Root 开始。息屏保留有效任务，唤醒时尽力恢复。 |

旧不变量的替代关系：NAV-002 → NAV-008、NAV-009；NAV-003 → NAV-009、NAV-010；NAV-004 → NAV-010、NAV-014。旧 ID 保留在 Git 历史中，不再表示当前结构。

## 官方 Settings 适配

官方 Settings 使用组合式 IApp Adapter 转发官方回调；其自带可见 Back 不叠加系统控件，Edge Back 与按钮均委托官方 Back 动作。适配只开放统一 Page 观察与 Back，绑定锁定版页面映射，不为 Settings 提供通用 push/pop。未知屏或 Flow 不可读取时报告错误、关闭适配 Back；原 App 和 PWR Home 仍可使用。选择理由见 [ADR-0012](../../adr/0012-official-settings-keeps-its-navigation-owner.md)。

## App Card 与生命周期

App Card 是同一 App 在 Home Space 的呈现角色，位于完整 App 页面栈之外。Home Space 管 Card 的配置和横滑；ESPocket 管 Card UI 的创建、可见、暂停、释放以及再次可见时的数据请求。App 管 Card 内容、纵向交互、轻量操作和持久业务数据。Card 与完整 App 共享 App ID，不要求共享同一个内存实例。

用户配置以 `App ID + Card ID` 为身份；同一 Card ID 最多一张。App 卸载或更新移除 Card ID 时，配置删除并记录原因。Quick Settings 和 Launcher 不是可替换 Card。App Card 的注册与生命周期由 ESPocket 产品层提供，Brookesia 的 App 生命周期和 GUI 接口仍作为底层能力。

首版 Runtime Card 使用声明式 GUI 和受限元数据绑定，由 ESPocket 在真实安装身份下管理独立文档，不启动另一套 Runtime。Native Card 使用 CardModel 回调；共同导航和生命周期语义不依赖语言接口相同。独立 JS 业务回调延后，见 [ADR-0014](../../adr/0014-runtime-card-starts-declarative.md)。

## AI Native

Assistant 调用 Home、Back 或打开 App 时仍进入对应 Owner 的语义接口。打开 App 的 Action 需要明确 Root 或目标 Page；Back 仅在可返回的子页面可用。页面快照可以作为经过授权的系统 Context，但页面参数、表单内容和整条栈不自动暴露。

Exposure Decision：开放稳定导航语义，不开放 GUI 坐标点击、原始手势注入、LVGL 对象或 App 私有导航数据。

## Code Anchors

- [System](../../../firmware/components/espocket_system/include/espocket/system.hpp)
- [System implementation](../../../firmware/components/espocket_system/src/system.cpp)
- [Settings Navigation Adapter](../../../firmware/components/espocket_system/include/espocket/settings_navigation_adapter.hpp)
- [CircularShell](../../../firmware/components/shell_circular/include/espocket/circular_shell.hpp)
- [Brookesia GUI runtime](../../../firmware/managed_components/espressif__brookesia_gui_interface/src/runtime.cpp)

## 非目标

- 规定手势识别算法、动画时长或 UI Widget 层级。
- 建立跨 App 返回链或保证 App 后台驻留。
- 在 ESPocket 产品层复制 System Core 的 App 安装与运行状态机。
