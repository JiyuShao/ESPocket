# 04 — App 契约

## 目的

本契约定义 Native App、Runtime App 与第三方 App 共同遵守的用户体验，使执行模型差异不会改变导航、显示恢复、资源回收和 AI 能力的含义。

## 用户结果

- 用户在不同 App 中获得一致的 Root、Page、Back 与 Home 行为。
- App 被回收后重新启动会回到可靠起点，不会恢复失效页面。
- 用户可以在圆屏上清楚地阅读信息并完成主要操作。
- App 停止后，旧实例的 UI 和 AI 能力不会继续响应。

## 产品要求

| ID | Requirement |
|---|---|
| APP-003 | PWR Home 必须离开可见 App 并返回 Watch Face，不得被 App 阻塞。 |
| APP-004 | 未被回收的 App 在息屏后唤醒时应该恢复原页面；目标失效时必须返回 Watch Face。 |
| APP-005 | App 停止、崩溃、重启或被回收后，下一次启动必须从 Root 开始。 |
| APP-006 | App 不得依赖后台驻留保证长期业务；可靠计时、播放、连接或持久状态必须独立于页面实例。 |
| APP-008 | 主要内容和操作必须位于圆屏安全区域；关键按钮不得依赖屏幕四角。 |
| APP-009 | 信息型、控制型、列表型和工具型页面必须突出一个主要任务，避免手机式 Toolbar、Tabs 与 Bottom Navigation。 |
| APP-010 | Native App 与 Runtime App 必须对相同输入和生命周期事件给出相同的产品语义。 |
| APP-021 | 每个 App 必须声明唯一 Root 和稳定的 Page 类型 ID；Root 不提供 Back，子页面 Back 返回 App 页面栈中的上一页面。 |
| APP-022 | App 决定 Page 转移，ESPocket 保存导航栈并提供 push、pop、replace 和回 Root 操作；首版不提供跨 App 返回链。 |
| APP-023 | ESPocket 默认在子页面提供可见 Back 与 Edge Back；App 可整体关闭两者，但多级 App 必须自带调用同一 Back 语义的可见控件。App 使用 ESPocket 标准 Back 控件时不得再叠加第二个可见 Back。 |
| APP-024 | App 可以暂缓普通 Back 并自行显示确认；待决时重复 Back 不得重复提交，超时取消并报告错误，PWR Home 始终可立即离开。 |
| APP-025 | PWR Home 后再次打开 App 必须从 Root 开始；未被回收的 App 在息屏唤醒时尽力恢复原 Page。 |

旧要求的替代关系：APP-001 → APP-021、APP-023；APP-002 → APP-022；APP-007 → APP-023。旧 ID 保留在 Git 历史中，不再表示当前产品要求。

## AI Native

| ID | Requirement |
|---|---|
| APP-011 | App 的 AI 能力只在对应 Running Instance 存活期间可用；实例结束后 Assistant 不得继续调用或观察它。 |
| APP-012 | 需要跨 App 生命周期存在的 AI 能力必须表现为独立的长期系统能力，不能依附于页面或已停止实例。 |
| APP-013 | Native App 与 Runtime App 对等的产品能力必须使用一致的 AI 语义、结果和风险规则。 |
| APP-014 | UI 与 Assistant 可以调用同一产品 Action，但每次调用必须按实际调用者和有效授权独立判断。 |
| APP-015 | Assistant 请求已停止 App 的实例能力时，产品必须明确报告不可用；只有正常启动流程可以创建新实例。 |

## App Card

| ID | Requirement |
|---|---|
| APP-016 | App 可选地声明专门的 App Card 界面；未声明的 App 不出现在可添加 Card 列表。Card 与完整页面共享 App 身份，但导航位置不同。 |
| APP-017 | Home Space 拥有 App Card 的横滑导航；App Card 可提供轻量信息与直接操作，多级流程必须进入完整 App 页面。 |
| APP-019 | App Card 的创建、可见、暂停与释放由系统管理。App 不得依赖 Card 或完整页面持续前台来保证长期业务。 |
| APP-020 | 用户决定是否添加、移除和排序 App Card；卸载 App 时系统必须移除其 Card。 |
| APP-026 | App 可以声明多个稳定 Card ID；同一 Card ID 在 Home Space 最多出现一次，不同 Card ID 可以同时添加。App 更新删除 Card ID 时系统必须移除对应配置并记录原因。 |
| APP-027 | App Card 可以声明打开完整 App 的目标 Page；Root 必须位于该目标 Page 的栈底。目标 Page 失效时必须打开 Root 并记录错误。 |
| APP-028 | Card 与完整 App 使用同一 App 身份和持久业务数据，不要求共享同一内存实例。Card 离屏时其 UI 可暂停，再次可见时由系统请求新数据。 |

## 非目标

- 规定页面类、回调 Interface、资源对象或 Runtime 内部实现。
- 为四类页面建立模板框架。
- 保证后台驻留或完整页面状态恢复。
- 建立通用 App-to-App 导航历史。
