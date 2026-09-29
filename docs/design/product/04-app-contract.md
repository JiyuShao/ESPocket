# 04 — App 契约

## 目的

本契约定义 Native App、Runtime App 与第三方 App 共同遵守的用户体验，使执行模型差异不会改变导航、显示恢复、资源回收和 AI 能力的含义。

## 用户结果

- 用户在不同 App 中获得一致的 Root、Detail、Back 与 Home 行为。
- App 被回收后重新启动会回到可靠起点，不会恢复失效页面。
- 用户可以在圆屏上清楚地阅读信息并完成主要操作。
- App 停止后，旧实例的 UI 和 AI 能力不会继续响应。

## 产品要求

| ID | Requirement |
|---|---|
| APP-001 | 每个 App 必须有一个 Root；Detail Back 必须回到父页面，Root Back 必须回到直接 Launch Source。 |
| APP-002 | App 只能保留一个直接 Launch Source，不得维护任意长度的跨 App 历史链。 |
| APP-003 | PWR Home 必须离开可见 App 并返回 Watch Face，不得被 App 阻塞。 |
| APP-004 | 未被回收的 App 在息屏后唤醒时应该恢复原页面；目标失效时必须返回 Watch Face。 |
| APP-005 | App 停止、崩溃、重启或被回收后，下一次启动必须从 Root 开始。 |
| APP-006 | App 不得依赖后台驻留保证长期业务；可靠计时、播放、连接或持久状态必须独立于页面实例。 |
| APP-007 | App 可以使用 Tap、普通滚动、普通横滑与 Long Press，但不得占用 Edge Back 或阻塞 PWR。 |
| APP-008 | 主要内容和操作必须位于圆屏安全区域；关键按钮不得依赖屏幕四角。 |
| APP-009 | 信息型、控制型、列表型和工具型页面必须突出一个主要任务，避免手机式 Toolbar、Tabs 与 Bottom Navigation。 |
| APP-010 | Native App 与 Runtime App 必须对相同输入和生命周期事件给出相同的产品语义。 |

## AI Native

| ID | Requirement |
|---|---|
| APP-011 | App 的 AI 能力只在对应 Running Instance 存活期间可用；实例结束后 Assistant 不得继续调用或观察它。 |
| APP-012 | 需要跨 App 生命周期存在的 AI 能力必须表现为独立的长期系统能力，不能依附于页面或已停止实例。 |
| APP-013 | Native App 与 Runtime App 对等的产品能力必须使用一致的 AI 语义、结果和风险规则。 |
| APP-014 | UI 与 Assistant 可以调用同一产品 Action，但每次调用必须按实际调用者和有效授权独立判断。 |
| APP-015 | Assistant 请求已停止 App 的实例能力时，产品必须明确报告不可用；只有正常启动流程可以创建新实例。 |

## 非目标

- 规定页面类、回调 Interface、资源对象或 Runtime 内部实现。
- 为四类页面建立模板框架。
- 保证后台驻留或完整页面状态恢复。
- 建立通用 App-to-App 导航历史。
