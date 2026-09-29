# M5 Launcher 同步策略

## 状态

- 策略：已针对锁定的 Brookesia 0.8.x API 定义完成
- 实现：推迟到 M5 包信任门可以强制执行之后
- M6：尚未进入

本文定义 Circular Shell 如何反映已安装的 Runtime App，同时避免把 ESPocket 变成通用 Shell 框架，也不重复实现 Brookesia 的 App Manager。

## 目标

- 保持产品自有入口稳定。
- 只有可信 Core 安装完成提交后，才显示动态安装的 Runtime App。
- 在安装、更新、卸载和重启发现后确定性地更新 Launcher。
- 不得跨包替换或重启缓存 `AppId`。
- 所有 Core 调用都必须发生在 Shell/System 的 App task 路径上。
- 失败时保持关闭，同时不破坏 Launcher、Home、Settings 或 Store。

## 入口归属

### 固定产品入口

以下入口继续静态写在 Circular Shell 的 JSON 中：

- `Hello Native`，在它仍作为平台验证 App 期间保留；
- `Hello Runtime`，在它仍作为构建预置的 Runtime 验证 App 期间保留；
- Settings；
- App Store。

这些入口的位置、样式和 action 属于产品装配。动态同步不得删除、重排、遮蔽或替换它们。

因此，固定 manifest ID 集合是唯一的排除列表：

```text
espocket.app.hello
espocket.app.hello_runtime
brookesia.general.settings
brookesia.general.app_store
espocket.shell.circular
```

不得为这五个入口增加 Provider Registry 或第二套 Launcher 模型。

### 动态入口

动态 Launcher 入口只能来自满足以下条件的 Core `AppInfo`：

- `manifest.kind == Runtime`；
- `manifest.visible == true`；
- 不在固定 manifest ID 集合中；
- 已通过包信任策略准入，并存在于 Core 已提交的 App 列表中。

V0.x 不动态准入 Native App。新增产品 Native App 仍然属于显式的产品装配变更。

在 [`package-trust.md`](package-trust.md) 可以强制执行之前，任何下载或本地 `.bpk` 都不具备进入动态区域的资格。

## 唯一事实来源

Core 的 `list_apps()` 是 Launcher 唯一的实时事实来源。Circular Shell 不得根据以下信息推断安装状态：

- Store catalog 或 cache 文件；
- 存储中存在的已下载 `.bpk`；
- Shell 自行发现的目录；
- 过期的 App Store UI 状态；
- 之前缓存的 `AppId`。

Store 报告请求执行的操作；Core 报告已经提交的安装状态。

## 同步模型

使用完整、确定性的对账，不建立自定义事件 Registry 或增量 App 数据库。

1. Core 操作提交后，`espocket::System::on_app_installed()` 和 `on_app_uninstalled()` 递增共享的 Launcher 同步 generation。
2. Circular Shell 只从 composition root 接收 generation provider 或窄接口的 dirty notifier。App 和 Service 不增加对 Circular Shell 的依赖。
3. 现有的 Shell-owned 周期 timer 在 Core App task 上观察 generation 变化。
4. 发生变化时，Shell 调用 `context.system_service().list_apps()`，筛选符合条件的动态 App，构建完整目标快照，并对账动态容器。
5. 只有每个 create/bind/destroy 步骤都成功后，Shell 才记录该 generation。
6. 失败时，Shell 保留或恢复最后一个完整视图，不记录包秘密，并在之后的 timer tick 重试。

Shell 还应在 `on_start()` 中、GUI document 就绪后执行一次对账。这覆盖重启发现，以及在 Shell 自身启动前已经安装的 package App。

V0.x 预期 App 数量较少，完整快照也能自然修复遗漏或合并的 hook 通知，因此优先采用完整快照。不需要持久化 Launcher 索引。

## GUI 实现边界

复用 Brookesia JSON UI template 和现有公共 API：

```cpp
context.gui().create_view(template_id, parent_path, instance_id);
context.gui().destroy_view(absolute_path);
context.gui().set_binding_values(...);
context.gui().subscribe_action(action, handler);
```

在 Circular Shell 现有 JSON document 中新增一个可滚动动态容器，以及一个 Runtime App 行/按钮 template。不得用 Native LVGL 创建动态入口，不得修改 GUI backend，也不得在运行时重新生成整份 Shell JSON。

即使动态区域为空或同步失败，固定产品区域也必须保持可用。

### 稳定的实例标识

GUI `instance_id` 不得直接嵌入 manifest ID。应把 manifest ID 编码为适合 JSON view path、确定且抗碰撞的标识，例如：

```text
app_<SHA-256(manifest_id) 前 16 字节的小写十六进制>
```

当前完整快照需要维护 instance ID 到 manifest ID 的内存映射。如果发现碰撞，应使本次对账失败，而不是显示或启动错误 App。

不得使用 `std::hash`，因为它的稳定性不是持久化或 API 保证。该映射从 `list_apps()` 重建，永不持久化。

## 排序与名称

动态入口按以下顺序排序：

1. 使用 Core 当前语言解析后的显示名；
2. manifest ID，作为确定性的次级排序键。

名称解析复用 `resolve_app_display_name(manifest, language)`。空的本地化名称按照 Core 现有规则依次回退到英文名称、其他非空名称、`manifest.name`，最后回退到 manifest ID。

改变名称、语言、可见性或图标的更新，在下一次完整对账中生效。V0.x 不保留用户自定义顺序；目前没有文件夹、收藏、最近使用或拖拽排序的明确需求。

## 图标策略

只有 `has_app_icon_image(manifest)` 为 true，且资源已经在 Core 安装时注册，才使用 Core 全局作用域的 App icon 资源；否则渲染标准的纯文本 Runtime 行。

图标缺失或加载失败不得隐藏其他方面均符合条件的 App。动态图标的 preload/release 必须跟随 Shell view 生命周期，并且不得比对应动态入口存活更久。

## Action 路由

使用一个共享的动态 action，例如：

```text
shell.open_dynamic_runtime
```

Action handler 使用 GUI `Event.path`，把当前快照的 instance ID 解析为 manifest ID。它只记录一个待处理 manifest ID，不在 GUI callback 中直接调用 Core。

现有 Shell timer 在 App task 路径消费待处理启动请求：

1. 再次调用 `list_apps()`；
2. 把 manifest ID 解析为当前可见的 Runtime `AppInfo`；
3. 如果目标不存在、已隐藏、不再是 Runtime 或不再通过信任准入，则拒绝；
4. 使用**当前** `AppId` 调用 `start_app()`；
5. 恰好一次地清除待处理请求。

这可以防止点击和分发之间发生卸载或更新时启动错误对象。包替换可能产生新的 `AppId`；manifest ID 才是稳定的 Launcher 身份。

只保留一个待处理动态启动。已有请求待处理时忽略第二次点击。这足以满足 V0.x 单前台 App 模型。

## 操作语义

### 安装

- Core 先完成信任验证与激活提交。
- 只有 GUI/resource 准备成功后，Core 才调用 `on_app_installed()`。
- System 递增 generation。
- Shell 对账加入符合条件的 App。
- 如果 Launcher 渲染失败，App 仍保持已安装，但不能以半完成状态暴露；重试不会重新安装它。

### 更新

- 信任门事务必须保留旧 App，直到新版本完成提交。
- Core 根据最终上游事务 API 的定义发出 uninstall/install lifecycle hook。
- 多个 hook 通知可以合并为一次 generation 变化。
- Shell 完整快照只能显示最后提交的旧版本或已经提交的新版本，绝不能同时显示两者。
- 行身份保持为 manifest ID；名称和图标可以变化。
- 待处理点击必须重新解析到当前已提交的 `AppId`。

### 卸载

- 如果 App 位于前台，Core 必须在卸载提交前停止它。
- Core 移除 App，随后调用 `on_app_uninstalled()`。
- System 递增 generation。
- Shell 销毁动态行，并释放所有 Shell-owned icon preload。
- 如果待处理点击指向已移除的 manifest ID，分发过程应拒绝并清除它。
- Store cache 与 trust receipt 的清理遵循包信任策略；Launcher 不管理文件。

### 重启

- Core 在 Shell 启动前完成可信 built-in 与动态 App 发现。
- Shell 初始对账使用由此产生的 `list_apps()` 快照。
- 不读取或恢复 Launcher 状态文件。
- 被信任、兼容性或 receipt 检查拒绝的 App 不会进入 `list_apps()`，也不会显示。

### 安装或更新失败

- 没有 `on_app_installed()` 提交通知，就没有新入口。
- 事务更新失败时保留旧的已提交 App，因此对账也保留它的入口。
- Store 可以解释失败原因；Launcher 不显示缓存中或待处理的包。

### Runtime 生命周期失败

- 启动失败时入口仍保持已安装，并通过现有 lifecycle restoration 返回 Launcher。
- 停止失败继续使用 ESPocket 现有的 fail-closed keyboard latch。
- 生命周期失败不等于卸载，也不会移除入口。

## Hook 与启动时序

Core 在修改 App record 时调用安装 hook。Hook 实现不得同步调用 `list_apps()` 或修改 Shell GUI；它只能标记 generation dirty，然后返回。

Hook 调用栈退出后，Shell 才从自己的 timer 执行对账。这样可以保持所有权和 task 顺序简单，并避免对 Core 的重入访问。

在当前 System setup 中，ESPocket 的 `on_init()` 会先安装 Circular Shell，Core 随后才扫描 package App；但这些 package 的 `on_app_installed()` hook 仍发生在 Shell 启动并获得 GUI context 之前。共享 generation counter 可以安全记录这些早期提交；Shell 的初始完整对账使精确的早期计数并不重要。

## 对账失败规则

对账不得留下新旧混合的列表。

V0.x 使用最小的安全方案：

1. 在内存中构建并验证目标模型；
2. 在临时动态容器或 generation 专属子树下创建并绑定替换实例；
3. 所有实例成功后，再切换 visibility/mount ownership 并销毁旧子树；
4. 任一步失败时，销毁临时子树并保留旧子树；
5. 仅在提交后更新 `applied_generation`。

如果当前 GUI API 无法原子交换两个子树，就在完整替换子树就绪前保留旧列表。只有在同一个 timer turn 内能够恢复旧快照时，才允许动态区域短暂为空。整个过程中固定产品入口必须始终可用。

重复失败的日志应限速，并且只在 generation 变化或适度退避后重试，不能每 50 ms 自旋。

## 容量与布局策略

466×466 产品 UI 需要边界明确的可见区域，而不是手机式网格。

- 固定入口保持在顶部；
- 动态入口使用纵向可滚动区域；
- 行文字在安全宽度处省略；
- M5 不增加动画、文件夹、最近使用、badge 或拖拽排序；
- Launcher 不设置硬性的 App 数量安全上限——准入由包与存储策略控制——但渲染必须足够惰性，以满足实测内存预算。

首个实现只创建当前完整快照需要的行。只有实测 App 数量或 PSRAM 使用量确实需要时，才增加 viewport virtualization。

## 并发与所有权不变量

- System 拥有 App 生命周期和 dirty generation。
- Circular Shell 拥有 Launcher 展示和动态 view map。
- Store 拥有 catalog/download UI，但绝不写 Launcher 状态。
- Runtime App 不能直接注册 Launcher 入口。
- GUI callback 只记录 intent；Shell timer 调用 Core。
- Manifest ID 是稳定身份；`AppId` 在分发时解析。
- Hidden App 和隐藏 Shell 永不显示。
- 没有包信任门，就不显示任何动态 App。

## 验收矩阵

主机与静态测试必须覆盖：

- 筛选逻辑排除 hidden、Native、固定、不兼容和不可信 App；
- 确定性排序与显示名回退；
- 确定性的 instance ID 与碰撞拒绝；
- 初始快照为每个符合条件的 manifest ID 恰好创建一个入口；
- 重复或合并的安装通知保持幂等；
- 更新修改 metadata 时不产生重复入口，并解析新的 `AppId`；
- 卸载移除入口并取消待处理启动；
- 点击/卸载竞态不能启动过期 `AppId`；
- 对账失败保留上一个完整快照；
- 语言变化触发名称重排或重建；
- Shell 重启从 Core 重建，且不使用持久化 Launcher 状态。

包信任和在线 HTTP 解锁后的真机验收：

1. 安装一个签名且兼容 ESPocket 的 Runtime App；入口恰好出现一次；
2. 启动它；Home 返回 Launcher；
3. 更新它；入口仍只有一个，并启动新版本；
4. 强制更新失败；旧入口和旧版本仍可启动；
5. 重启；不打开 Store，可信入口也会重新出现；
6. 卸载；入口消失，重启后仍不出现；
7. 重复安装、更新和卸载，同时监控 heap/PSRAM 与 GUI cleanup；
8. 全程验证固定的 Hello、Settings、Store 入口仍可使用。

## 实现门槛

在以下条件全部成立前，不实现动态 Launcher 暴露：

- 公共 Core 安装与发现路径已经强制执行包信任门；
- 实际上游 API 已定义更新回滚语义；
- 至少有一个签名包支持 `systems: ["espocket"]`；
- 在线 Store 的取消问题已经修复并完成真机回归。

在此之前，当前固定 Launcher 是正确的 fail-closed 产品行为。
