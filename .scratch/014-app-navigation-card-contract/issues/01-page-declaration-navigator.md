# 01 — 声明与 App Page Navigator

**What to build:** 在 ESPocket 产品层校验 App Root、全部 Page ID 与可选 Card 目标，提供执行模型无关的唯一 Page 栈和 Native 接入；Runtime 语言绑定留给 ticket 04。

**Blocked by:** [006/03 Home 与显示真机验收](../../006-m6-home-display/issues/03-run-hardware-acceptance.md)（已完成）。

**Status:** resolved

- [x] 无 Root、重复 ID 或 Card 指向未声明 Page 时安装校验失败；声明身份在 App 更新后稳定。
- [x] Root 不可 pop，运行时未知 Page 不修改原栈；Card 目标运行时失效降级 Root 并记录错误。
- [x] PWR Home 后再打开从 Root 开始，息屏唤醒保留有效 Page，实例失效清除旧栈。
- [x] Navigator 从同一状态给出当前 `pageId`、`canBack`、`backPending`，不暴露参数或整条栈。
- [x] Navigator 接口不依赖 Native GUI 实现细节；Native Adapter 对操作和错误使用该接口，Runtime Adapter 留给 ticket 04。
- [x] Hello 与 Store 接入共同 Navigator，官方 Settings 按明确适配例外读取真实 Page；移除示例专用页面名分支，声明与实例生命周期使用同一事实源。

## Comments

- 2026-10-02（夜间）：补充 `update_declaration` 的停止态原子更新与稳定 App/Root 身份校验；真实 C++ 用例覆盖更新拒绝不改旧声明、保留 Card ID 更新目标、删除 Page/Card、Root 降级和跨版本迟到 token。已完成项按主机行为测试、System/Native 源码与既有 Settings 记录勾选；不把组件更新入口视为已接入通用安装/卸载更新生命周期，第一项仍保留开放。PWR/唤醒此前 Native 样机已确认，当前结构重构的集中 smoke 仍归 013/04、06。详见 [夜间记录](../../013-firmware-structure-refactor/records/2026-10-02-overnight-frontier.md)。

- 2026-10-02：用户确认 [ADR-0012](../../../docs/adr/0012-official-settings-keeps-its-navigation-owner.md) 的 Settings 限定例外，最后一项从「全部接入共同 Navigator」改为普通 Native App 用 Navigator、官方 Settings 适配真实页面。Settings Adapter 源码与主机／资源兼容测试已完成，整包及真机结果见 [适配记录](../records/2026-10-02-settings-adapter.md)；本 ticket 仍保留未完成的更新迁移及验收条件。

- 2026-10-02：原最后一项要求 Native 与 Runtime Adapter 同时完成，与 M7 Native source gate → M8 Runtime 验收顺序冲突。当前 ticket 先提供共同 Navigator 和 Native 接入；Runtime Adapter 的对等验证移到 ticket 04，保留共同语义目标。
- 2026-10-02：已加入执行模型无关的 `PageNavigator`、Native 示例 Page 声明与画面适配，主机接口测试覆盖声明错误、Root、push/pop、Card 直达与目标缺失、停止重启和呈现失败。Native 真机路径、App 更新时 ID 迁移与运行时诊断仍待验证；见 [M7 记录](../records/2026-10-02-page-navigator-source.md)。
- 2026-10-02：Card ID 失效或目标 Page 呈现失败时均停在 Root、返回 `target_unavailable` 并调用诊断回调；System 已为 Native 示例接入日志，主机测试与整机构建通过。源码镜像 `c6e6e0fa...` 尚未刷入。App 更新时 Page/Card ID 迁移与通用 App 接入仍待完成。
- 2026-10-02：System 的 PageNavigator 注册与生命周期查找已改为 App ID，移除了 Hello 专用 manifest 分支，整包构建通过。官方 Settings/Store 都是 `final` App；Settings 的 `current_page_` 私有，但 System Core 提供 `gui_get_screen_flow_state(appId, flow)` 只读查询。接入时应从该上游状态读取实际 Page，避免复制第二套栈；可见 Back 与 App 内业务动作仍需产品层 Adapter 验证。此 ticket 保持开放。
- 2026-10-02：Store 作为 Root 单页 App 注册 `store.root`；官方 Store 继续呈现标签和弹窗，Root 无默认 Back。镜像 SHA-256 `0379976803ccab31738993c02e5d4f096345857a8e6ca24cb6227d491dac1835` 整包构建、刷写校验和自动启动通过；Store 页面内行为尚未在这版做真机操作，Settings Page 适配仍开放。

## Resolution

- 2026-10-02：共同 Navigator/Native 安装与 Back 组件条件已完成；逐项证据见 [Native 安装收尾](../records/2026-10-02-native-installation.md) 与其中链接的声明更新、Settings 适配和 Native 用户观察。
- 声明更新核心、安装校验、停止/卸载清理与 Root/待决 Back 由实际源码测试覆盖。Runtime 绑定、待决确认 UI 样例与真实软件包构建仍归 04，Card 注册/更新配置归 03；未声称这些路径已完成。
- 013 结构重构 smoke、007/03 与 008/03 硬件验收仍独立待决；本次未刷写新镜像，也没有新增真机通过项。
