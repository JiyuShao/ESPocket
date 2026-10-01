# Navigation Surfaces

Sequence: 007

Status: active
Blocked by: [006/03 Home 与显示真机验收](../006-m6-home-display/issues/03-run-hardware-acceptance.md)（已完成）；Native 源码依赖见 ticket 02。

## Problem Statement

Home 与 Display State 建立后，ESPocket 需要一套以手表为中心、贯穿 Cards、Quick Settings、Launcher 与 Native App 的导航闭环。

## Solution

实现真实 Surface content、App 子页面默认可见 Back 与 Edge Back，Root 无 Back，同时保留 App horizontal gesture，并让 PWR Home 到达 Watch Face。Home Space 的反向滑动按[交互模型](../../docs/design/product/03-interaction-model.md)执行。

## User Stories

1. 作为用户，我希望 Watch Face 两侧具有稳定、不循环的 Cards 边界。
2. 作为用户，我希望 Quick Settings 改变真实设备状态。
3. 作为用户，我希望子页面 Back 回到上一 Page，App Root 靠 PWR Home 回表盘。
4. 作为 App，我希望普通 horizontal swipe 不被误判为 Edge Back。
5. 作为测试者，我希望 brightness 与 Wi-Fi 变化在真机上得到证明。

## Implementation Decisions

- 当前固定 Cards 保持单页内容；未来 App Card 可由同一 App 提供专门界面，遵循 [ADR-0011](../../docs/adr/0011-app-root-has-no-back.md)。
- ESPocket 默认在 App 子页面提供可见 Back 与 Edge Back；Root 无 Back。App 可同时接管默认入口并定制返回 UI/手势，不要求可见按钮；按 ADR-0013 使用统一 Back 语义。
- PWR Home 从 App 回 Watch Face；不通过 Root Back 恢复启动来源。
- Battery、Brightness、Wi-Fi 与 Settings 提供最小真实内容。
- Brightness 使用当前选中的真实 Display output，不使用固定 ID。

## Testing Decisions

- 真机验收依赖已完成的 Home 与显示验收票；源码前置由 014 的 Navigator/Back 票提供。
- 在真机上验证完整导航闭环与每条 edge path。
- 证明真实 Wi-Fi 与 brightness 变化，不能只观察控件文案。

## Out of Scope

Runtime App 契约验证、App Card 注册与动态配置、任意 App-to-App history 与 dynamic Launcher。

## Tickets

- [01 — 修复 brightness output identity](issues/01-fix-brightness-output-identity.md)
- [02 — 关闭系统导航源码与构建条件](issues/02-close-navigation-source-gates.md)
- [03 — 完成系统导航真机验收](issues/03-run-navigation-hardware-acceptance.md)

## Comments

- 2026-10-01：原方案要求「实现真实 Surface content、Edge Back 与一个直接 Launch Source」，并让「Back 返回直接启动 App 的 Surface」；原决定还包括「Cards 保持 single-page content，不变成 nested App」及「只保存一个直接 Launch Source」。经 [ADR-0011](../../docs/adr/0011-app-root-has-no-back.md) 决策，App Root 改为无 Back，子页面使用 Page 栈；当前固定 Card 仍保持单页，App Card 留待后续。上文为当前待实施范围，原方案保存在此作为决策历史。

## 当前结果与完成条件

亮度 OutputId 已修复；两轮系统导航及 Wi-Fi/亮度真实变化已取得样机证据。剩余源码、Card 边界和 Settings/Store 组合条件归 [02](issues/02-close-navigation-source-gates.md)，未覆盖的单次路径及最终镜像核对归 [03](issues/03-run-navigation-hardware-acceptance.md)。已有两轮证据保留，不重复要求完整循环。触控镜像、已刷入镜像与最新仅构建镜像分别以 records 中的 identity 为准。

## 记录

- [2026-10-02-brightness-output-id](records/2026-10-02-brightness-output-id.md)
- [2026-10-02-source-gate-progress](records/2026-10-02-source-gate-progress.md)
- [2026-10-02-two-navigation-loops](records/2026-10-02-two-navigation-loops.md)

- 2026-10-02：按已接受的 [ADR-0013](../../docs/adr/0013-app-controls-back-presentation.md) 修正此前残留的多级 App 必须有可见 Back 描述；不改变 Root、导航事实或硬件验收门槛。
