# App Page、Card 与 Back 开发 API（目标 v1）

本文规定 ESPocket 开发框架向 Native 与 Runtime App 提供的共同语义和首版接口。实现范围、未完成条件与证据见[App 导航与 Card 工作项](../../.scratch/014-app-navigation-card-contract/spec.md)。产品约束见 [App 契约](../design/product/04-app-contract.md)，Owner 分工见[导航架构](../design/architecture/05-navigation-runtime.md)。

当前 Native 源码已提供 `PageDeclaration`、`PageNavigator` 和 `PageSnapshot` 的第一版 C++ 接口。Native 示例由 App 声明 Page，并把 Navigator 请求映射到自己的 Brookesia Screen Flow；ESPocket System 按 App ID 注册 Navigator，管理栈的启动、停止和 Back 请求。官方 Store 由产品层声明单个 `store.root`，其标签与弹窗属于 Root 内部状态。子页面默认可见 Back 与 Edge Back 已在 Native 样例接入；`request_back`、`complete_back`、`expire_back` 提供允许、取消、暂缓及超时语义。官方 Settings 已在源码接入限定版本的页面快照与 Back Adapter，保留上游导航事实源，不建立第二份栈；真机已确认 Settings 子页面 Edge Back 正常、没有可见 Back，按 App 自主呈现规则接受。Runtime v1 JSON 边界与 Owner 队列已进入源码；动态 Card 接入与页面参数交付仍按后续工作项实施，本页其余内容是目标契约。

## 职责边界

| 角色 | 拥有 | 调用或声明 |
|---|---|---|
| App 开发者 | App 身份、Page/Card 内容、业务数据与 Action、页面转移意图、未保存内容确认 UI | 声明 Page 与 Card；调用导航和 Back API；提供 Card 数据和轻量操作 |
| ESPocket 开发框架与运行框架 | 声明校验、普通 App Page 栈、默认 Back、Edge Back、Card 位置和呈现生命周期、只读页面语义 | 向 Native/Runtime 暴露同一契约，向 Shell 与测试提供同一状态事实；官方 Settings 使用下文限定适配 |
| Brookesia System Core / GUI / Service | App 安装与运行实例、GUI 与底层服务 | 由 ESPocket Adapter 使用；App 不为产品导航改动上游组件 |
| Shell | Home Space Surface、Card 横滑、Launcher 与 Quick Settings 手势、临时 Overlay | 打开 App 或目标 Page，不写 App 页面栈 |

## 外部旧包的开发者兼容运行

[ADR-0018](../adr/0018-developer-mode-allows-unsigned-packages.md) 允许开发者模式下的外部旧包暂不接入本导航契约。平台只保证 App 生命周期与 PWR Home；内部页面与返回仍由 App 管理。缺少接入时页面快照必须明确不可用，不能伪造 Root、Page ID 或 canBack，也不能接受指定 Page 打开或统一页面 Back。此例外不改变新开发 ESPocket App 的声明要求，不把缺失声明与已经提供但无效的声明混为一类。

## 安装时声明

每个 App 声明一个 `appId`、一个 `rootPageId` 和全部 Page 类型的稳定 `pageId`。`pageId` 在该 App 命名空间内唯一；同一页面类型的不同业务数据共用 ID。业务参数不作为 Page ID，也不进入系统快照。安装时缺 Root、ID 重复、Card 指向未声明 Page 或声明不一致时，安装校验失败并给出可诊断错误。

App 可选地声明多个 Card 类型。每个 Card 使用稳定 `cardId`，并可声明打开完整 App 时的目标 `pageId`；未指定目标时打开 Root。Card ID 以 `appId + cardId` 形成配置身份，同一 ID 在 Home Space 最多出现一次，不同 ID 可以并存。只有声明 Card 的 App 出现在可添加列表。用户决定左右 Card 的添加、移除和排序；Quick Settings、Launcher 的位置固定。卸载 App 或新版不再声明某 Card ID 时，ESPocket 移除该配置并记录原因。

App 级 Back 呈现声明有两种模式：`framework` 为默认；`appOwned` 同时关闭 ESPocket 的可见默认 Back 与 Edge Back。所有 App 选择 `appOwned` 时，自行决定返回 UI 与手势，例如边缘或上下滑动；不要求可见按钮，自定义入口调用 ESPocket 的 `requestBack`。选择默认模式时，页面可放置 ESPocket 标准 Back 控件；系统识别后不再叠加第二个可见 Back，Edge Back 仍可用。Root 在两种模式下均无 Back。

第一版 C++ 声明使用 `BackPresentation::Framework` 或 `BackPresentation::AppOwned`。App 自行放置 ESPocket 标准 Back 控件时声明 `uses_standard_back_control=true`，避免 Shell 再叠加控件；`AppOwned` 不要求声明可见控件；`uses_standard_back_control` 是 App 的呈现承诺；完整 App API 与控件注册机制仍待定版。

Native 核心提供 `update_declaration(PageDeclaration)`：仅在 Navigator 已停止、无页面任务时更新，运行中返回 `DeclarationInUse`。App ID 与 Root Page ID 保持稳定，否则返回 `IdentityMismatch`；新声明仍按安装规则完整校验，失败保留旧声明。Page/Card 列表可重排、新增或移除，保留的 ID 不按数组位置重新编号；页面语义是否仍相同由 App 作者保证。更新后不恢复旧栈或待决 Back，下一次启动从同一 Root 开始；旧 Card 不存在时保持既有 Root 降级和诊断。此入口不负责软件包安装、Card 配置删除或替换 Presenter，分别由安装 Adapter、Card Registry 和对应语言绑定承担；Runtime 安装和导航已接入，软件包替换迁移仍未完成，不能把组件测试算作软件包更新验收。

Native 产品装配使用 `System::install_navigated_app(app, declaration, presenter)`，返回 `InstalledPageApp` 中的 Core App ID 与共享 Navigator。身份与声明先校验，通过后才调用 Core 的真实安装入口；Core 安装失败时透传错误、不发布注册。App 保存 Navigator 的弱引用，页面适配器由 App 实现。System 按 Core App ID 处理开始、停止、失败和卸载；卸载清空旧栈、token、注册与系统 UI 回调。安装入口在系统初始化或 Core 管理操作的串行调用上下文执行，不从原始 GUI 输入回调或任意并发线程调用；注册表的锁不表示 Core 安装接口支持任意并发。`install_native_page_app` 是此入口的底层 Core 边界，App 作者使用 System 入口，以保证注册和生命周期连接。

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

## Runtime v1 绑定

可见 Runtime App 在资源目录提供 `navigation.json`，格式见 [版本化 schema](schemas/runtime-pages-v1.schema.json)，完整样例见 [Hello Runtime 声明](../../firmware/runtime_apps/hello/src/res/navigation.json)。`version` 当前只能为整数 1；未知字段、类型错误和未声明目标被拒绝，Root 必须属于 pageIds，Card ID 与转移的 from/to 配对不能重复。App ID 必须与 package manifest 相同。缺少声明或校验失败使真实 Core 安装失败；不会回报一个假 Root。

`presentation.screenFlow` 指向 App 的实际 Brookesia Screen Flow；v1 Page ID 与该 Flow 的 Screen ID 一致。`transitions` 为每个需要的 from/to 配对声明一个实际 action。启动核对 Flow 初始状态与 Root；转移前后核对实际 GUI 状态。Flow 不可读取或与 Navigator 不一致时，快照报 `invalid_state`，关闭该次系统 Back，不从 GUI 另建第二份栈。App 的页面动作调用 Navigator，不直接调用 TriggerScreenFlow 绕过它。

JS 入口是 `espocketNavigation.dispatch(JSON.stringify(request))`，返回 Promise，成功值是 UTF-8 JSON 字符串，失败为下面的错误编码。对象与数组通过 JSON 字符串跨越官方 NativeValue 边界；不传 App ID，由官方 Runtime 调用上下文确定真实调用者。App 可包装为 `JSON.parse(await ...)`。当前 Native 与 Runtime 导航仅接受稳定 Page ID；业务参数保留在 App 数据中，Runtime 传入额外 parameters 返回 bad_request，不能静默丢弃。目标参数交付能力仍待扩展。

| request | 作用 |
|---|---|
| `{operation:"push", pageId}` / `{operation:"replace", pageId}` | 使用共同 Navigator 压栈或替换页面 |
| `{operation:"pop"}` / `{operation:"resetToRoot"}` | 页面业务主动导航；Root 不可 pop |
| `{operation:"requestBack"}` | 与默认可见 Back、Edge Back 相同的确认入口 |
| `{operation:"setBackDecision", decision:"allow"或"cancel"或"defer"}` | 设置本次运行的 Back 策略；待决期间不能更改 |
| `{operation:"completeBack", token, allow}` | 允许或取消待决请求；token 是十进制字符串，allow 是 boolean |
| `{operation:"snapshot"}` | 返回 appId、pageId、canBack、backPending 和 App 私有 pendingToken |

`pendingToken` 没有待决时为 null，存在时为十进制 uint64 字符串，避免 JS Number 精度损失；它不进入 USB 的最小测试快照。每次运行默认 allow，重新打开不保留确认开关或旧 token。System 对普通 Back 计时 15,000ms，到期取消并记录 back_timeout；迟到确认返回 stale_request。15 秒起点是 Owner 收到 Back 的时间。

Runtime 调用只入队，由现有 App 回调任务执行实际 Navigator/GUI 操作；不在 JS 调用线程等待 Owner。最多 16 个待处理请求，2,000ms 内未执行返回 timeout；无前台调用者返回 not_started，旧前台代次返回 stale_request。PWR 优先于队列消费。关闭 System 取消队列，卸载移除绑定。锁定 JS backend 在后续回调刷新 Promise completion，因此 ESPocket 为已绑定 Runtime 提供 50ms Core timer，名字保留为 espocket.navigation.completion；即使 App 没有用户输入或业务 timer，Promise 也能完成。Core 在停止时回收 timer。App 不自行实现 completion pump；样例的另一个 100ms timer 只刷新确认 UI，不拥有栈或超时。

Navigator 的同源错误编码为 invalid_declaration、not_started、unknown_page、at_root、root_page、target_unavailable、presentation_failed、back_pending、back_cancelled、back_timeout、stale_request、declaration_in_use、identity_mismatch。绑定另区分 unsupported_version、bad_request、unsupported、busy、timeout、system_unavailable、page_adapter_unavailable、invalid_state。重复 Back 被拒绝，确认失败不 pop；普通 push/pop/replace/reset 可改变业务导航并使旧 token 失效，两种语言保持共同 Navigator 语义。

## 官方 Settings 兼容边界

按 [ADR-0012](../adr/0012-official-settings-keeps-its-navigation-owner.md)，`SettingsNavigationAdapter` 持有官方 App，转发原有生命周期、动作与计时器回调。页面事实从官方 `settings_content` Screen Flow 实时读取，映射到 `settings.root`、`settings.device`、`settings.wifi`、`settings.wifi_connect`、`settings.sound`、`settings.display`、`settings.more`、`settings.language`、`settings.time_zone`、`settings.debug`。这些是 ESPocket 的稳定 Page ID；业务参数不进入快照。

Settings 的 Back UI 由官方 App 决定，可以不显示；系统不叠加按钮。系统 Edge Back 与官方 App 提供的 Back 动作均委托 `settings.header.back`，由官方 App 执行业务清理与页面转移。Root 不 Back，官方 App 不实现 ESPocket 的待决 token，快照的 `backPending` 为 false。Settings 内部未保存内容行为仍由官方 App 决定；普通 App 的 Back 待决契约不因此改变。System 的 `foreground_page_snapshot()` 对已接入的前台 App 提供同一 `PageSnapshot` 类型；无前台、未接入或无法观察时返回错误。该查询用于 App／系统调用线程，不用于原始 GUI 输入回调。

适配层仅缓存 GUI 手势所需的 Back 可用标志，不缓存导航栈；Shell 的 App 回调定期重新读取真实页面，执行 Back 前也重新读取。未知屏或不可读取 Flow 使快照报错并关闭适配 Back，不能报告为 Root。映射与动作名绑定 Settings 0.8.3，升级须通过 [固件兼容检查](../../firmware/README.md#测试)。深度界面／业务定制、Settings 的 push/pop 或 Card 直达并未因此提供。

## Back 请求

Root 不显示默认 Back，也不响应 Edge Back。子页面上的 Back 进入 `requestBack()`；App 可立即允许、取消，或返回待决 token 以自行展示确认界面。ESPocket 在待决期间拒绝重复 Back；App 对同一 token 只能完成一次。允许时系统执行一次 `pop()`，取消时保持当前 Page。超时自动取消并报告 `back_timeout`，不能强行丢弃用户编辑。

PWR Home 不经过 App Back 回调，也不受确认界面阻塞：它取消待决 token、结束当前导航任务并显示 Watch Face。App 停止或崩溃同样使 token 失效；迟到的允许或取消返回 `stale_request`，不得改变新任务。App 自定义 Back 控件或手势必须调用相同入口，不可只切换 GUI 而不更新框架栈。

Native Reference App 的 Detail 提供 `Back confirm: Off/On` 开关，默认 Off 保持立即返回。开启后使用默认 Back 或 Edge Back，会保持 Detail、暂停重复 Back，并提示选择 `Allow Back` 或 `Cancel Back`；两者调用共同 Navigator 的 `complete_back(token, allow)`。未有待决时点击确认按钮报告不可用，不执行 pop。15 秒超时由 System 调用 Navigator 的 `expire_back`，App 的 100ms 状态 timer 只更新提示、清理已失效的本地 token，不另设超时或页面栈。停止时释放 timer 和回调，重新打开关闭确认开关，旧运行的确认状态不能写入新运行。该路径源码和组件验证完成，设备验证仍归 008/03，Runtime 同等确认样例已随 014/04 进入源码，真机结果仍由 008/03 持有。

## Card 注册与配置组件

当前 C++ 核心提供 [CardRegistry](../../firmware/components/espocket_navigation/include/espocket/card_registry.hpp)，只管理声明身份和左右配置，不保存 Page 栈、App 运行状态或 GUI 对象。它与 PageNavigator 复用 `validate_page_declaration`，避免 Card 与安装使用不同校验规则。System 已连接 Core 安装/卸载、NVS 配置和 Shell 呈现；声明式 Runtime Card 提供者已接入；package 替换迁移仍待真实更新事务入口。

| 接口 | 结果 |
|---|---|
| `register_app(PageDeclaration)` | 校验后登记 App 可提供的 Card；重复 App 拒绝。无 Card 声明的 App 不出现在 available_cards。 |
| `update_app(PageDeclaration)` | App 必须已登记且 Root ID 不变；失败保持原声明/配置。成功移除已删除 Card 的配置，保留其余身份和用户顺序。 |
| `uninstall_app(appId)` | 移除 App 声明与其已配置 Card；不影响其他 App。真实 Core 卸载回调使用此入口。 |
| `available_cards()` / `target_page(CardKey)` | 查询已声明 Card；空目标解析为 Root，不执行页面转移。 |
| `add(CardKey, side, index)` | 在左右序列指定索引插入；同一 appId+cardId 在两侧合计最多一次。 |
| `move(CardKey, side, finalIndex)` | 移动已有配置，索引指删除原位置后的最终序列位置；可换侧。 |
| `remove(CardKey)` | 只移除配置，不卸载 App 或删除其可添加声明。 |
| `replace_configuration(CardConfiguration)` | 完整校验身份和跨侧重复后原子替换；任何失败保留旧配置。 |
| `configuration()` | 返回左右稳定身份列表的拷贝；不会以声明数组顺序重新编号。 |
| `set_removal_handler(handler)` | 提交后通知 UserRemoved、AppUninstalled 或 RemovedByUpdate；回调在锁外运行，可查询已提交配置。 |

`CardSide` 只允许 Left/Right，不配置 Quick Settings 或 Launcher。`CardError` 区分无效声明、未知 App/Card、重复登记/配置、未配置、错误位置/方向和身份不一致。Registry 方法内部加锁；移除回调应快速完成且不抛异常。回调是配置移除的历史事实，不是另一个运行实例或后台订阅。配置快照现在由下节的 Store 接入 NVS；实际 Card 可见生命周期仍不能由 Registry/Store 组件测试代替。

## Card 配置存储与 Core 接入

`System::configure_cards(CardConfiguration)` 是串行 App Owner 的完整配置入口，`card_configuration()` 与 `available_cards()` 返回拷贝。配置仅包含左右数组中的稳定 appId/cardId，不包含 Quick Settings、Launcher、页面栈或 GUI 对象。增删和排序通过修改这份拷贝并提交完整候选完成；Card 编辑器不属于当前范围。身份与跨侧重复完整校验后，先保存 NVS，再发布 Registry 更新；保存失败保留现有配置，不能将 ACK 当作已改变。

[Card 配置 schema v1](schemas/card-configuration-v1.schema.json) 与生产 codec 使用整数 version 1、left/right 数组，所有未知字段与跨侧重复拒绝。最大编码 16,384 字节。设备保存于 espocket/cards_v1，启动在 Core package 安装后恢复。未知 App/Card、坏编码或读取失败报告错误、保留原始 NVS，不猜测它是卸载，也不覆写为一个空配置。

普通 Native 和可见 Runtime 的安装声明现在登记到同一个 Registry。真实 Core 卸载删除对应配置并记录 AppUninstalled；失败的 NVS 保存报告错误，不复活已卸载 App。停止后的 Native 声明更新使用 `System::update_navigated_declaration`，复用 Navigator 身份规则，再更新 Registry，移除删除的 Card 并记录 RemovedByUpdate，保留其他稳定 ID 与顺序。更新已生效后保存失败仍报告错误，不能声称回滚了 Owner 事实。

Runtime package 替换与 Native 的声明更新是不同入口。锁定 Core 将替换实现为 uninstall/install，现有 hook 不带原因；尚未提供保留 Card 配置的产品更新事务。不能把普通卸载判成更新，或声称官方 Store 替换已经验证迁移。该事务仍未完成；Native 和声明式 Runtime 提供者、Shell 呈现已经接入，真实显示验收保留。

## Native Card 内容接口

App 使用 [CardModel](../../firmware/components/espocket_navigation/include/espocket/card_model.hpp) 和 `CardModelFactory` 提供内容，并把工厂作为 `System::install_navigated_app` 第四个参数。工厂按稳定 Card ID 创建专用模型，不启动完整 App、不创建第二份页面栈。`view()` 提供 Brookesia GUI JSON、资源目录、绝对 Screen 路径和动作名称；`on_show/on_refresh/on_pause/on_action` 在 System Owner 上执行，不得抛异常、重入配置或保留失效的 `CardUi` 引用。`CardUi::set_text` 只作用于自己的文档，可见时有效。

框架挂载专用文档，订阅点击并交给有期限、有代际校验的 Owner 队列；离屏和息屏取消订阅、暂停模型，恢复时重新订阅并请求数据。GUI 迟到事件仍绑定旧代际，不能作用于恢复后的槽位。App 声明动作 `espocket.card.open` 即可打开该 Card 的最新目标；框架先暂停 Card，再建立完整 App Root 和目标 Page。Native Reference App 提供 summary→Root、detail→Detail 两个 Card，数据来自自己的 manifest；没有承诺后台常驻或业务持久化。

左右已配置序列替代该方向原有示例 Card，空序列保留系统 Battery/Brightness 示例。横滑向外浏览序列，向内在首个 Card 回 Watch Face；纵向交互保留给 App。App Card 有轻微返回方向提示，没有顶部状态栏。Card 编辑器不在本轮范围，正式固件不自动把所有声明加入用户配置。

## 声明式 Runtime Card v1

按 [ADR-0014](../adr/0014-runtime-card-starts-declarative.md)，首版不执行独立 JS Card 实例。完整 App 继续使用既有 JS 导航绑定；Card 的显示与刷新由 ESPocket 提供。包内 `navigation.json.cards` 声明稳定 Card ID 与目标 Page；有 Card 声明时，资源目录必须提供 `cards.json`，其 appId 与 Card ID 集合完全一致。无声明的包不创建 Card 提供者。

[Runtime Card schema v1](schemas/runtime-cards-v1.schema.json) 的字段如下：

| 字段 | 约束与含义 |
|---|---|
| version / appId | 整数 1；匹配 Core 安装身份。 |
| cards | 最多 32 个 Card，ID 不重复且完整匹配 navigation.json。 |
| cardId / screen | 稳定 Card ID；screen 是 GUI 根 viewScreen 的绝对路径，例如 /card。 |
| gui | 内联 Brookesia GUI 文档，只含 version 与 assets，assets 恰有一个匹配 screen 的 viewScreen；不提供外部文档导入或 screenFlow。 |
| bindings | 可选，最多 32 个文本绑定；path 在该 screen 内且不重复，source 仅 app.name 或 app.version。 |

整个声明最大 65,536 字节。路径段使用字母、数字、下划线或连字符，拒绝空段、越级路径和跨 screen 绑定。GUI 的 action 字段只接受 `espocket.card.open`；它打开 navigation.json 中对应 Card 的目标，而不是在 GUI 内指定另一 App/Page。未知字段、版本、身份、绑定来源和动作被拒绝，错误进入真实 Core 安装失败结果，不登记半套 Card。

每次 Card 再次可见，模型重新读取当前 Core App 元数据并更新声明的文本；安装消失、身份不一致或 GUI 更新失败时暂停并报告错误。离屏/息屏释放订阅，不创建 App JS timer、宿主模块或后台任务。静态内容、纵向滚动与样式由 App 的内联 GUI 提供，渲染属性由 Brookesia GUI 在呈现时校验。第一版不读取表单、私有业务参数、任意 Service 或持久业务文件，不支持自定义 JS 轻量业务动作；这些能力须独立扩展数据源与授权协议。

实际包样例见 [cards.json](../../firmware/runtime_apps/hello/src/res/cards.json) 与 [navigation.json](../../firmware/runtime_apps/hello/src/res/navigation.json)。summary 打开 Root，detail 打开 Detail；框架先暂停 Card，再在唯一 Navigator 上建立 Root 与目标 Page。PWR Home 后普通重开从 Root 开始；真实视觉与触控证据仍由 014/05、008/03 持有。

## App Card 生命周期

当前提供 [CardSession](../../firmware/components/espocket_navigation/include/espocket/card_session.hpp) 的同步 C++ 生命周期组件，已接 Shell GUI、Native 与声明式 Runtime Card 提供者。一个 Session 管理一个呈现槽位，状态为 Empty、Paused 或 Visible；不是 Core Running Instance，也不保存 Page 栈。`show(key)` 只接受已声明且已配置的 Card，首次创建内容，暂停后再次显示调用 `show` 和 `refresh` 请求新数据；已可见的重复 show 不重复刷新。切换 Card 先暂停并销毁旧内容。`pause()` 保留当前 UI，`release()` 和析构释放 UI 与订阅。

App 绑定实现 `CardContent::show/refresh/pause`，析构负责资源回收。创建失败保持 Empty；显示或刷新失败暂停内容并报告明确错误，可由 Shell 再次 show 重试。`open_app(launcher)` 重新读取 Registry 的当前目标，先暂停，再调用完整 App 启动入口；启动失败保持 Paused，由 Shell 明确决定恢复呈现。Launcher 仍需使用现有 Navigator 建立 Root 和目标路径，这个组件不建立第二份栈。配置已删除或声明已卸载时拒绝启动并释放内容。

System/Shell 装配应在 GUI Owner 任务串行调用 Session 和 Registry 更新，并把 Registry 的移除通知转发给 `invalidate(key)`；它仅释放匹配的 Card，不影响其他 Card。内容、工厂与启动回调不得抛异常或在回调中修改 Registry；重入 Session 操作返回 Busy。当前 refresh 是同步能力，未提供后台异步结果提交 API；System 在原有串行 App 回调任务调度模型与动作，GUI 回调只入队。组件测试不代替实际界面验收。

Card 与完整 App 使用同一 App 身份和持久业务数据，但可以是不同内存实例。ESPocket 管理 Card UI 的创建、可见、暂停与释放。离屏后 Card UI 可暂停或销毁；再次可见时框架请求新数据。App 提供 Card 内容、订阅来源和轻量操作；可靠计时、网络状态与其他长期业务放在 App 持久数据或 Service，不以 Card UI 常驻为前提。进入完整 App 时 Card 暂停，PWR Home 返回 Watch Face。

Home Space 拥有 Card 横滑。Card 内点击、纵向滚动和轻量操作归 App；需要多级交互时打开完整 App。App 不通过 Card 拦截 PWR Home 或改变左右 Card 顺序。

## 页面开发指导

遵循 [App 产品契约 APP-008–APP-010](../design/product/04-app-contract.md) 和[导航 Owner 分工](../design/architecture/05-navigation-runtime.md)，每个 Page 突出一个主要任务。以下是布局和行为指导，不增加页面类继承体系。

| 页面用途 | 呈现与操作 | 导航和数据边界 |
|---|---|---|
| 信息型 | 中部优先显示一个主数值或短结论；来源、更新时间作为辅助内容。 | 读取 Service 或持久业务数据；再次可见重新请求，不把控件文字当状态源。需要更多细节时 push 已声明 Detail。 |
| 控制型 | 一个主要操作配合明确的当前值、执行中和失败反馈；点击区域留在圆屏可操作区域。 | Action 交给实际 Owner，成功后读真实状态；投递成功不表示操作完成。未保存修改可暂缓 Back，PWR Home 不等待确认。 |
| 列表型 | 纵向单列，每行只承担一个明确入口或操作；短标签优先，避免边缘裁切。 | 同一 Detail 类型共用稳定 Page ID，业务项目放参数而不是生成 Page ID。完整 App 的纵向滚动归 App；Home Space 横滑仍归 Shell。 |
| 工具型 | 当前任务、结果与一个主操作分层；把复杂流程拆为明确的 App Page。 | push/pop/replace 经共同 Navigator；Root 无 Back。进行中的长期计时或网络任务放 Service/持久业务层，不依赖当前 Page 或 Card 存活。 |

圆屏中部是标题、主值和主操作的优先区域；首版采用短内容和单列布局，检查首尾项、长文案及控件是否被圆形边缘裁切。不要用手机式 Bottom Navigation、密集 Toolbar 或 Tabs 承载主要流程。需要 Back 时使用框架默认入口，或按已声明接管规则实现同一语义，避免重复按钮；Root 的离开入口是 PWR Home。

App 只维护业务数据和呈现对象，不维护供系统读取的第二份页面栈。开始时连接回调/订阅，暂停可停止只影响可见内容的工作，停止时释放 timer、订阅和 GUI 引用；迟到回调应检查运行身份或使用不会写入新运行的状态对象。后台驻留不作保证，App/Card UI 被释放后可靠业务仍由其持久状态或 Service 负责。Native Hello 的确认样例可参考 timer 与 token 清理；Runtime Page 绑定已提供版本化 JSON API；Card 模型的 C++ 回调不能直接当作现成 JS 导出。

### Runtime App 生命周期

Runtime 入口脚本在锁定 backend 中可能于同一 JS realm 再次执行。样例使用 IIFE 私有作用域，只导出 `globalThis.brookesia_app`；作者不要依赖 stop 清空顶层 `const/let` 声明。`on_start` 初始化瞬时确认状态，`on_stop` 使旧运行的异步结果失效；同一 realm 二次加载和迟到结果由真实样例测试覆盖。

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

## 默认边缘手势与 Root

Root 的 canBack、默认 Back 和 edge_back_enabled 仍为 false。默认返回由框架负责时，框架消费达到阈值的边缘返回轨迹，避免滑动误点 Root 按钮，不发起页面返回。AppOwned 仍把自定义边缘手势交给 App；普通非边缘横滑、上下滚动不受此规则接管。C++ Navigator 的 framework_owns_back 查询该运行任务的默认返回责任，与实际 Back 可用性分开；System 只发布由 Owner 更新的手势标志给 Shell，不复制页面栈或更改快照字段。

## 系统消息弹窗与主题

App 可通过 Brookesia `AppContext::system_service()` 的 `show_message_dialog`、`update_message_dialog`、`hide_message_dialog` 请求系统消息弹窗。保存返回的 Request ID，并在结果回调中处理按钮索引、角色与关闭原因；不能把弹窗当作 Page 或修改页面栈。Core 管理请求归属、排队与 App 停止清理，ESPocket System 转发公开 hooks，Circular Shell 提供圆屏 Overlay 呈现。

当前呈现支持最多三个按钮、可滚动说明与 `auto_close_ms`。普通手势不穿透 modal；PWR Home 仍可结束前台 App，Core 随之关闭其弹窗。Shell 的 LVGL 回调只记录选择，结果在 App 任务中交给 Core，App 不应自己从 LVGL 回调调用生命周期操作。

产品在安装会预载文档的 App 前注册 dark/light，并从 Core 的持久偏好恢复当前主题。锁定 GUI Runtime 的主题设置只作用于新文档；官方 Settings 选择主题时先保存偏好，再通过系统确认请求重启。选择“稍后”或通过 Home 关闭确认不撤销已保存的偏好。App 引用共享 `app.page`、`app.card` 等 styleRefs 时消费产品主题；App 的硬编码颜色与自有样式不会自动改写。具体设备验收和未完成显示检查保存在工作票与 records，不作为上述 API 的额外承诺。

### Shell 与 App 的主题职责

产品在安装 App 之前注册并恢复 Brookesia GUI 的主题。Shell 的 Watch Face、Launcher、Quick Settings 与 Shell 自有 Card 用 `styleRefs` 引用产品主题，不保存第二份主题偏好。App Page 与 App Card 优先引用 `app.page`、`app.cardTitle`、`app.caption` 等主题样式，遵循下文主题开发规范；尺寸、字体和布局仍由 App 声明。硬编码颜色的 App 需要自行适配，Shell 不递归改写它的控件。

官方 Settings 当前保存主题后询问是否重启；Later 只推迟重启，已保存的主题偏好仍在。当前 GUI 不支持给已创建文档即时重套主题，因此完整切换在重启后生效。

### 主题开发规范

本规范适用于新建或修改的 Shell Surface、Shell Overlay、Native/Runtime App Page 与 App Card。默认界面应消费当前主题，让浅色与深色模式共享同一份界面声明。

1. 优先复用产品已提供的语义样式，通过 `styleRefs` 引用 `app.page`、`app.card`、`app.cardTitle`、`app.cardSubtitle`、`app.caption`、`app.action` 和 `app.actionText` 等。局部样式可以调整尺寸与布局；不得用固定颜色覆盖主题样式以实现普通背景、文字、边框或交互状态。
2. 现有样式不满足需求时，优先使用 `${color.<语义路径>}` 颜色变量。普通界面按用途选择背景、表面、文字、边框、主色或状态色；不要依赖某个色阶恰好在当前主题中呈现的颜色。按钮背景与其文字必须成对定义，包括按下、禁用和选中等实际使用的状态。
3. 引用前确认变量或样式在产品支持的 dark/light 两份主题中都有定义。上游默认主题提供某个变量，不代表当前 ESPocket 产品主题已提供该变量；不得依赖未验证的回退。缺少通用 token 时，在产品主题中补充同名语义定义，再由界面引用。当前配置入口是 [light_theme.json](../../firmware/components/espocket_system/resources/light_theme.json) 与 [dark_theme.json](../../firmware/components/espocket_system/resources/dark_theme.json)。
4. 新增样式或变量按用途命名，例如卡片背景、辅助文字或成功状态；不要以十六进制颜色或 light/dark 命名。两种主题保持相同的语义和状态含义，分别调整明度、对比度与层次；产品主题中的具体色值可以自定义，不要求沿用上游默认配色。
5. 品牌标识、照片、插画和业务数据中具有固定含义的颜色可以保留固定色值。App 自有配色仍须适配两种模式，检查周围背景、文字与操作的可读性；在资源旁说明固定颜色的用途。普通界面颜色不得以品牌或装饰为由绕过主题适配。

复用样式的最小示例：

```json
{
  "type": "label",
  "id": "subtitle",
  "styleRefs": ["app.cardSubtitle"],
  "labelProps": {"text": "最近更新"},
  "style": {"textAlign": "center"}
}
```

开发验收应检查两种主题中的页面背景、主次文字、按钮及其状态、图标和边框；App Page 与 App Card 分别检查，不能只验证其中一种形态。确认所有新增引用在两份主题中可解析，并检查局部样式是否覆盖了主题颜色。设备视觉验收按当前实现，在保存主题并重启后进行；使用 token 不代表已创建文档支持即时切换。上述要求是开发规范，既有界面的迁移与真机结果仍由对应工作票记录。
