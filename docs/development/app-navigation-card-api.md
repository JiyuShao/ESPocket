# App Page、Card 与 Back 开发 API（目标 v1）

本文规定 ESPocket 开发框架向 Native 与 Runtime App 提供的共同语义。能力尚未完整实现在固件中；实施顺序见[App 导航与 Card 工作项](../../.scratch/014-app-navigation-card-contract/spec.md)。产品约束见 [App 契约](../design/product/04-app-contract.md)，Owner 分工见[导航架构](../design/architecture/05-navigation-runtime.md)。此处的操作名用于表达接口，C++ 类型、JS 绑定和字段编码将在实现时固定。

当前 Native 源码已提供 `PageDeclaration`、`PageNavigator` 和 `PageSnapshot` 的第一版 C++ 接口。Native 示例由 App 声明 Page，并把 Navigator 请求映射到自己的 Brookesia Screen Flow；ESPocket System 按 App ID 注册 Navigator，管理栈的启动、停止和 Back 请求。官方 Store 由产品层声明单个 `store.root`，其标签与弹窗属于 Root 内部状态。子页面默认可见 Back 与 Edge Back 已在 Native 样例接入；`request_back`、`complete_back`、`expire_back` 提供允许、取消、暂缓及超时语义。官方 Settings 已在源码接入限定版本的页面快照与 Back Adapter，保留上游导航事实源，不建立第二份栈；真机已确认 Settings 子页面 Edge Back 正常、没有可见 Back，按 App 自主呈现规则接受。Runtime 绑定、动态 Card 生命周期和生产级线程/参数编码仍按后续工作项实施，本页其余内容是目标契约。

## 职责边界

| 角色 | 拥有 | 调用或声明 |
|---|---|---|
| App 开发者 | App 身份、Page/Card 内容、业务数据与 Action、页面转移意图、未保存内容确认 UI | 声明 Page 与 Card；调用导航和 Back API；提供 Card 数据和轻量操作 |
| ESPocket 开发框架与运行框架 | 声明校验、普通 App Page 栈、默认 Back、Edge Back、Card 位置和呈现生命周期、只读页面语义 | 向 Native/Runtime 暴露同一契约，向 Shell 与测试提供同一状态事实；官方 Settings 使用下文限定适配 |
| Brookesia System Core / GUI / Service | App 安装与运行实例、GUI 与底层服务 | 由 ESPocket Adapter 使用；App 不为产品导航改动上游组件 |
| Shell | Home Space Surface、Card 横滑、Launcher 与 Quick Settings 手势、临时 Overlay | 打开 App 或目标 Page，不写 App 页面栈 |

## 安装时声明

每个 App 声明一个 `appId`、一个 `rootPageId` 和全部 Page 类型的稳定 `pageId`。`pageId` 在该 App 命名空间内唯一；同一页面类型的不同业务数据共用 ID。业务参数不作为 Page ID，也不进入系统快照。安装时缺 Root、ID 重复、Card 指向未声明 Page 或声明不一致时，安装校验失败并给出可诊断错误。

App 可选地声明多个 Card 类型。每个 Card 使用稳定 `cardId`，并可声明打开完整 App 时的目标 `pageId`；未指定目标时打开 Root。Card ID 以 `appId + cardId` 形成配置身份，同一 ID 在 Home Space 最多出现一次，不同 ID 可以并存。只有声明 Card 的 App 出现在可添加列表。用户决定左右 Card 的添加、移除和排序；Quick Settings、Launcher 的位置固定。卸载 App 或新版不再声明某 Card ID 时，ESPocket 移除该配置并记录原因。

App 级 Back 呈现声明有两种模式：`framework` 为默认；`appOwned` 同时关闭 ESPocket 的可见默认 Back 与 Edge Back。所有 App 选择 `appOwned` 时，自行决定返回 UI 与手势，例如边缘或上下滑动；不要求可见按钮，自定义入口调用 ESPocket 的 `requestBack`。选择默认模式时，页面可放置 ESPocket 标准 Back 控件；系统识别后不再叠加第二个可见 Back，Edge Back 仍可用。Root 在两种模式下均无 Back。

第一版 C++ 声明使用 `BackPresentation::Framework` 或 `BackPresentation::AppOwned`。App 自行放置 ESPocket 标准 Back 控件时声明 `uses_standard_back_control=true`，避免 Shell 再叠加控件；`AppOwned` 不要求声明可见控件；`uses_standard_back_control` 是 App 的呈现承诺；完整 App API 与控件注册机制仍待定版。

Native 核心提供 `update_declaration(PageDeclaration)`：仅在 Navigator 已停止、无页面任务时更新，运行中返回 `DeclarationInUse`。App ID 与 Root Page ID 保持稳定，否则返回 `IdentityMismatch`；新声明仍按安装规则完整校验，失败保留旧声明。Page/Card 列表可重排、新增或移除，保留的 ID 不按数组位置重新编号；页面语义是否仍相同由 App 作者保证。更新后不恢复旧栈或待决 Back，下一次启动从同一 Root 开始；旧 Card 不存在时保持既有 Root 降级和诊断。此入口不负责软件包安装、Card 配置删除或替换 Presenter，分别由安装 Adapter、Card Registry 和对应语言绑定承担；Runtime 安装接入仍待 014/04，不能把组件测试算作软件包更新验收。

## Page 导航

普通 App 由 ESPocket 保存唯一 App Page 栈。App 通过以下语义操作决定转移；操作成功后，显示页面、Back 能力和测试快照从同一栈计算。App 不另存一份供框架使用的导航栈。官方 Settings 的限定适配例外见下节；它不提供这组栈操作。

| 操作 | 前提与结果 |
|---|---|
| `push(pageId, parameters)` | ID 已声明；在当前 Page 上压入目标。参数只交给 App 页面，不进入系统快照。 |
| `pop()` | 返回上一 Page；到 Root 时返回 `at_root`，不离开 App。 |
| `replace(pageId, parameters)` | 用目标替换当前非 Root Page；Root 不可被替换为另一个 Root。 |
| `resetToRoot()` | 清除 Root 以上页面，从声明的 Root 重新显示。 |
| `requestBack()` | 可见 Back、Edge Back 和 App 自带 Back 的共同请求入口；由待决处理后执行一次 `pop()`。 |

从 Card 打开目标 Page 时，ESPocket 先建立 Root，再让 App 构造到目标的路径；Root 始终是栈底。若 Card ID 已失效或目标 Page 在打开时呈现失败，ESPocket 保持 Root，并通过诊断回调记录 Card ID 与 `target_unavailable`。普通打开 App 和 PWR Home 后再次打开 App 从 Root 开始；息屏唤醒在实例有效时尽力恢复当前 Page。App 停止、崩溃或回收后，旧 Page 对象与待决 Back 均失效，后续启动建立新栈。首版不提供跨 App 返回链。

## 官方 Settings 兼容边界

按 [ADR-0012](../adr/0012-official-settings-keeps-its-navigation-owner.md)，`SettingsNavigationAdapter` 持有官方 App，转发原有生命周期、动作与计时器回调。页面事实从官方 `settings_content` Screen Flow 实时读取，映射到 `settings.root`、`settings.device`、`settings.wifi`、`settings.wifi_connect`、`settings.sound`、`settings.display`、`settings.more`、`settings.language`、`settings.time_zone`、`settings.debug`。这些是 ESPocket 的稳定 Page ID；业务参数不进入快照。

Settings 的 Back UI 由官方 App 决定，可以不显示；系统不叠加按钮。系统 Edge Back 与官方 App 提供的 Back 动作均委托 `settings.header.back`，由官方 App 执行业务清理与页面转移。Root 不 Back，官方 App 不实现 ESPocket 的待决 token，快照的 `backPending` 为 false。Settings 内部未保存内容行为仍由官方 App 决定；普通 App 的 Back 待决契约不因此改变。System 的 `foreground_page_snapshot()` 对已接入的前台 App 提供同一 `PageSnapshot` 类型；无前台、未接入或无法观察时返回错误。该查询用于 App／系统调用线程，不用于原始 GUI 输入回调。

适配层仅缓存 GUI 手势所需的 Back 可用标志，不缓存导航栈；Shell 的 App 回调定期重新读取真实页面，执行 Back 前也重新读取。未知屏或不可读取 Flow 使快照报错并关闭适配 Back，不能报告为 Root。映射与动作名绑定 Settings 0.8.3，升级须通过 [固件兼容检查](../../firmware/README.md#测试)。深度界面／业务定制、Settings 的 push/pop 或 Card 直达并未因此提供。

## Back 请求

Root 不显示默认 Back，也不响应 Edge Back。子页面上的 Back 进入 `requestBack()`；App 可立即允许、取消，或返回待决 token 以自行展示确认界面。ESPocket 在待决期间拒绝重复 Back；App 对同一 token 只能完成一次。允许时系统执行一次 `pop()`，取消时保持当前 Page。超时自动取消并报告 `back_timeout`，不能强行丢弃用户编辑。

PWR Home 不经过 App Back 回调，也不受确认界面阻塞：它取消待决 token、结束当前导航任务并显示 Watch Face。App 停止或崩溃同样使 token 失效；迟到的允许或取消返回 `stale_request`，不得改变新任务。App 自定义 Back 控件或手势必须调用相同入口，不可只切换 GUI 而不更新框架栈。

## App Card 生命周期

Card 与完整 App 使用同一 App 身份和持久业务数据，但可以是不同内存实例。ESPocket 管理 Card UI 的创建、可见、暂停与释放。离屏后 Card UI 可暂停或销毁；再次可见时框架请求新数据。App 提供 Card 内容、订阅来源和轻量操作；可靠计时、网络状态与其他长期业务放在 App 持久数据或 Service，不以 Card UI 常驻为前提。进入完整 App 时 Card 暂停，PWR Home 返回 Watch Face。

Home Space 拥有 Card 横滑。Card 内点击、纵向滚动和轻量操作归 App；需要多级交互时打开完整 App。App 不通过 Card 拦截 PWR Home 或改变左右 Card 顺序。

## 观察与错误

ESPocket 的只读页面语义至少包含 `appId`、当前 `pageId`、`canBack` 和 `backPending`。`canBack` 表示当前可接受一个 Back 请求；待决期间为 false，并同时显示 `backPending=true`。页面参数、表单值、私有 UI 树和完整栈不属于该接口。

| 错误类别 | 处理 |
|---|---|
| 未声明或重复 Page/Card ID | 安装校验失败，不发布不一致声明。 |
| 运行时导航目标无效 | 操作失败，保持原栈并报告 `unknown_page`。 |
| Root 收到 `pop` 或 Back | 返回 `at_root`，不触发 Home。 |
| Card 打开时目标 Page 失效 | 打开 Root 并记录 `target_unavailable`。 |
| Back 已待决 | 返回 `back_pending`，不重复调用 App。 |
| Back 超时或 token 过期 | 保持页面并报告 `back_timeout` 或 `stale_request`。 |

上述错误名是稳定语义类别；语言绑定中的精确枚举值、线程模型、参数编码和超时时长由实现工作项定版。Native 与 Runtime 对同一错误类别必须给出相同产品结果。
