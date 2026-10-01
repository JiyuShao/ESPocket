# 02 — 默认 Back 与待决分发

**What to build:** 子页面统一可见 Back 与 Edge Back、App 级整体禁用开关，以及可由 App 暂缓确认的 Back 请求。

**Blocked by:** [01 Page Navigator](01-page-declaration-navigator.md)。

**Status:** resolved

- [x] Hello、Settings 与 Store 的 Root 不显示或响应 Back；子页面默认可见 Back 与 Edge Back 触发同一 `requestBack`。
- [x] App 使用 ESPocket 标准 Back 控件时不出现双 Back；App 接管默认入口后可自定义返回 UI 或手势，不要求可见按钮，自定义入口使用统一 Back 语义。
- [x] 待决请求最多一个；重复 Back 不提交，超时取消并报告，迟到完成不改变新任务。
- [x] PWR Home、App 停止或崩溃使待决 token 失效，不能被 App 阻塞。

## Comments

- 2026-10-02（夜间）：修复待决 Back 被允许但页面呈现失败后，默认 Back 与 Edge Back 未恢复的状态发布漏洞。真实 C++ 接口测试覆盖失败保留 Detail、清除 pending、恢复入口和下一次请求成功；统一 host 检查通过。证据与后续执行顺序见 [夜间记录](../../013-firmware-structure-refactor/records/2026-10-02-overnight-frontier.md)。本票仍按 01 的依赖及未完成条件保持开放。

- 2026-10-02：官方 Settings 按 [ADR-0012](../../../docs/adr/0012-official-settings-keeps-its-navigation-owner.md) 的例外统一其自带按钮与 Edge Back，不叠加 Overlay，不复制栈，也不提供 ESPocket 待决 token；已实施 Root／未知页 guard 和回调委托，证据见 [适配记录](../records/2026-10-02-settings-adapter.md)。官方真实业务清理仍需真机检查。

- 2026-10-02：已实施 Navigator Back 请求状态机、呈现模式声明和 Shell 默认可见 Back。主机接口测试与整机构建通过；真机确认 Native Detail 默认 Back、Edge Back、Root 无 Back 与 PWR Home。暂缓 Back 样例仍待后续接入，证据见 [M7 记录](../records/2026-10-02-default-back-prototype.md)。

- 2026-10-02：按 [ADR-0013](../../../docs/adr/0013-app-controls-back-presentation.md) 取消多级 App 必须声明可见 Back 的安装限制。AppOwned 可使用自定义手势，通过同一 Back 请求返回；默认呈现仍可选。Settings 真机 Edge Back 正常，无可见按钮按 App 自主呈现接受。

## Resolution

- 2026-10-02：共同 Navigator/Native 安装与 Back 组件条件已完成；逐项证据见 [Native 安装收尾](../records/2026-10-02-native-installation.md) 与其中链接的声明更新、Settings 适配和 Native 用户观察。
- 声明更新核心、安装校验、停止/卸载清理与 Root/待决 Back 由实际源码测试覆盖。Runtime 绑定、待决确认 UI 样例与真实软件包构建仍归 04，Card 注册/更新配置归 03；未声称这些路径已完成。
- 013 结构重构 smoke、007/03 与 008/03 硬件验收仍独立待决；本次未刷写新镜像，也没有新增真机通过项。
