# App Page、Card 与 Back 开发契约

Sequence: 014

Status: active
Blocked by: M6 `PASS` for firmware integration; M7 source gate depends on the Page Navigator and Back dispatch work in this effort.

## Problem Statement

既有 `System::handle_back()` 针对示例 App 硬编码页面名，产品文档又把 Root Back 指向 Launch Source。这个模型不支持已确认的 Root 无 Back、动态 Page 顺序、App Card 直达目标 Page，以及 Native/Runtime 共用的可观察导航状态。App 作者也缺少清楚的职责和 API。

## Solution

由 ESPocket 提供安装时 Page/Card 声明、唯一 App Page 栈、统一 Back 分发和 Card 呈现生命周期。App 决定页面转移、Card 内容和未保存内容确认；Brookesia 继续管理 App 运行与 GUI 底座。先发布语义契约，具体 Native/Runtime 绑定及 Card 运行机制按 tickets 实现。

## User Stories

1. 作为 App 开发者，我能声明 Root、稳定 Page ID、可选 Card ID 和目标 Page，而不直接维护系统导航栈。
2. 作为用户，我在 App 子页面得到统一 Back，在 Root 不看到 Back，PWR 始终回 Watch Face。
3. 作为 Card 提供者，我能在 Home Space 展示轻量内容并打开完整 App 的目标 Page。
4. 作为测试者，我能从同一 Navigator 读取当前 Page、能否 Back 和 Back 待决状态。

## Implementation Decisions

- App 安装时声明唯一 Root 和全部 Page 类型；同一 App 可声明多个 Card ID，每个 ID 最多配置一次。
- ESPocket 持有 Page 栈，App 调用 push/pop/replace/resetToRoot。Card 目标失效时打开 Root 并记录错误。
- Root 无 Back；子页面默认有可见 Back 与 Edge Back。App 可整体禁用两个默认入口，多级 App 必须自带可见 Back。
- App 可以暂缓普通 Back，自行显示确认；框架拒绝重复请求，超时取消。PWR Home、停止和崩溃使待决 token 失效。
- PWR Home 后再次打开 App 从 Root 开始；息屏可恢复有效 Page；首版不提供跨 App 返回。
- Card UI 的可见、暂停和再次请求数据由框架处理；长期业务数据在 App 持久状态或 Service 中。

## Testing Decisions

- 声明校验、栈操作、Back 待决/超时/失效和 Card 配置迁移应有组件级测试。
- Native 与 Runtime 样例必须覆盖相同 Page/Back 语义；真实触控与可见控件仍按阶段门槛真机验证。
- 修改不能把 M7/M8 未验收的路径标记为已通过。

## Out of Scope

跨 App 返回链、Card 编辑器、后台常驻保证、通用 Widget SDK、具体 UI 动画和 Wi-Fi 测试通道。

## Tickets

- [01 — 声明与 App Page Navigator](issues/01-page-declaration-navigator.md)
- [02 — 默认 Back 与待决分发](issues/02-back-dispatch.md)
- [03 — App Card 注册与生命周期](issues/03-card-registry-lifecycle.md)
- [04 — Native/Runtime 样例与开发 API 定版](issues/04-samples-api-finalization.md)

## Further Notes

- [ADR-0011](../../docs/adr/0011-app-root-has-no-back.md)
- [App 产品契约](../../docs/design/product/04-app-contract.md)
- [导航架构](../../docs/design/architecture/05-navigation-runtime.md)
- [开发 API](../../docs/development/app-navigation-card-api.md)
- [M7 验收](../../docs/milestones/m7/acceptance.md)
- [M8 验收](../../docs/milestones/m8/acceptance.md)

## Comments

- 2026-10-02：原阻塞边为「M7 source gate for firmware integration」，但 M7 source gate 同时要求本 effort 的默认 Back 和唯一 Page 栈，构成循环依赖。M6 已 `PASS`，因此先实施 tickets 01–02 支撑 M7 的 Native 导航；App Card 与 Native/Runtime 全量绑定仍按后续 tickets 和阶段门槛验收。
