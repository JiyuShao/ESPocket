# 02 — 关闭系统导航源码与构建条件

**What to build:** Cards、Quick Settings、App 子页面默认可见 Back 与 Edge Back、Root 无 Back 和 PWR Home 形成一套可构建且绑定真实 capability 的导航闭环。

**Blocked by:** 01 — 修复 brightness output identity；[014/01 Page Navigator](../../014-app-navigation-card-contract/issues/01-page-declaration-navigator.md) 与 [014/02 Back dispatch](../../014-app-navigation-card-contract/issues/02-back-dispatch.md) 的 Native 路径。

**Status:** resolved

- [x] Brightness 修复后重新执行现有 host/static gate。
- [x] Card 与 Quick Settings capability error 以可预测方式失败。
- [x] 集成 [014/01](../../014-app-navigation-card-contract/issues/01-page-declaration-navigator.md) 与 [014/02](../../014-app-navigation-card-contract/issues/02-back-dispatch.md) 的 Native 路径，核对 Settings/Store 入口与系统 Surface 组合；Navigator/Back 实现和组件条件由两张前置票负责。
- [x] 复核当前固定 Shell Card 的单页边界及其与 App Card 呈现契约的分界。
- [x] Battery、Brightness、Wi-Fi 和 Settings 入口复用真实服务；重新确认操作失败的返回值、诊断和原控件反馈。
- [x] Home Space 反向滑动和 Launcher 顶部下拉不触发 App 的 Edge Back。
- [x] 不增加通用 Card SDK 或任意 history stack。

## Comments

- 2026-10-01：原任务为「Cards、Quick Settings、Edge Back 与直接 Launch Source 形成一套 clean、可构建且绑定真实 capability 的导航闭环」。[ADR-0011](../../../docs/adr/0011-app-root-has-no-back.md) 将 App Root Back 改为 PWR Home，当前任务范围按上文执行；保留原描述作为决策历史。
- 2026-10-02：原依赖只列 Brightness ticket，但此 ticket 的默认 Back、Root 无 Back 和页面栈需要先由 014/01–02 提供 Native 实现；014 原先反向等待 M7 source gate，已消除该循环。Runtime 绑定及 App Card 不计入本 M7 source gate。
- 2026-10-02：Brightness、Wi-Fi 失败路径现在返回错误并在原控件显示 unavailable；Host Navigator 与 Shell Action 检查、整机构建、最终镜像写入和自动启动检查通过，见 [源码进展记录](../records/2026-10-02-source-gate-progress.md)。Home Space 手势与 App Edge Back 在源码中由前台 App 状态隔离。默认 Back 的真机证据目前只覆盖 Native Hello；Settings/Store 尚未使用共同 Navigator，故此 ticket 保持开放。
- 2026-10-02：固定 Battery/Brightness Card 是 CircularShell 文档里的两个单页 Surface，Shell 持有其位置、手势和 capability 操作；Brightness 的 Settings 按钮只启动完整 App。App Card 的 `appId + cardId` 配置身份、Page 目标和生命周期仍由 014 契约定义，不从当前 Shell Card 推导通用 SDK。System 的 Native Navigator 查找已改按 App ID 注册并通过整包构建；Settings/Store 的上游私有页面状态仍需适配。

## 源码与构建检查结果

| 检查项 | PASS 条件 | 状态 |
|---|---|---|
| Surface model | Home Space、Launcher、Quick Settings 与 App Surface 关系符合主规范 | PASS（STATIC，dependency-gated） |
| Card boundary | 当前固定 Shell Card 为单页内容；未来 App Card 遵守专门的呈现与导航契约 | PASS（STATIC；当前 Shell JSON 与 014 契约复核） |
| Native Back | Detail → Parent；Root 无 Back；PWR Home → Watch Face | PASS（SOURCE/HOST：Native 共用 Navigator；Settings 限定 Adapter；物理覆盖归 03） |
| Gesture ownership | Home Space 反向滑动、Launcher 顶部下拉、App 默认 Back 不占用普通滚动和横滑 | PASS（SOURCE：前台状态隔离；Launcher 物理下拉归 03） |
| Existing services | Battery、Brightness、Wi-Fi、Settings 复用现有能力 | PASS（SOURCE：真实 Helper 与 launch Owner；额外物理入口覆盖归 03） |
| No premature framework | 无通用 Card SDK、插件框架或编辑器 | PASS（STATIC） |
| Build | 正常固件 clean build/link 成功 | PASS（2026-10-02，隔离目录构建；[记录](../records/2026-10-02-source-gate-progress.md)） |
| Static checks | JSON、脚本或项目既有检查全部通过 | PASS（JSON parse + `git diff --check`） |

## Resolution

- 2026-10-02：014/01–02 Native 条件完成，见 [安装与生命周期记录](../../014-app-navigation-card-contract/records/2026-10-02-native-installation.md)。Hello/Store 共用安装校验与 Navigator；Settings 从官方真实 Flow 提供 Page/Back，符合 ADR-0012，未复制栈。
- 复核 `shell_status.cpp`：Battery 使用 Device Helper 的实际电池状态，缺失时显示问号；Brightness 以真实 output ID 读写 Display Helper，失败返回 error 并在原控件显示 unavailable；Wi-Fi 以真实 GeneralState/TriggerGeneralAction 读写，失败同样返回并更新原控件。Settings 的三个 Shell 入口统一进入 System launch Owner，失败保留来源 Surface 并透传错误，Core/调用者记录诊断。
- Home Space、Launcher pull 与 App Edge Back 在同一 Shell 仲裁中按前台 App 状态隔离；没有新增第二套页面历史或 Card SDK。
- 最近统一 16 项 host tests、M2 parser 和 Markdown 通过，固件完整构建/链接通过；镜像 identity 见 [夜间记录](../../013-firmware-structure-refactor/records/2026-10-02-overnight-frontier.md)。没有刷写本轮镜像。
- 这里只关闭源码/构建条件；03 的 Card 边界、Launcher pull、Quick Settings → Settings、普通 App 横滑与最终物理 failure scan 等未覆盖项保持未完成，不从本表的 SOURCE/HOST PASS 推断硬件 PASS。
