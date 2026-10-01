# ADR-0010: App Card 是同一 App 在 Home Space 的专门形态

- Status: `superseded`
- Recorded: 2026-09-30
- Origin: 与用户讨论华为手表应用卡片和 ESPocket Home Space 后决定

本记录由 [ADR-0011](0011-app-root-has-no-back.md) 取代；App Card 的呈现角色继续成立，Root Back 回 Card 的旧决定不再适用。

## Context

Card 可由 Shell 内容或 App 占据。将完整 App 页面原样嵌入 Card 会让 Home Space 的横滑、App 内导航和前台生命周期争夺同一界面；把 Card 当作纯快捷入口又无法满足 App 直接成为 Card 的产品目标。

## Decision

App 可选择提供专门的 App Card 界面，与完整页面保持同一 App 身份。Home Space 拥有 Card 位置和横滑；App 拥有 Card 内容和轻量操作。进入完整 App 后，Root Back 回到来源 Card，PWR Home 回 Watch Face。用户管理左右 Card 的增删与顺序，Quick Settings 和 Launcher 位置固定。

## Consequences

- 需要 ESPocket 产品层的 Card 声明、呈现生命周期、来源恢复、配置和卸载清理机制。
- 当前固定 Shell Card 可继续存在；完整 App Card 机制留待后续，不并入 M7 真机交互样机。
- 不修改 Brookesia managed component 来实现产品专属契约。

参见 [App 契约](../design/product/04-app-contract.md)与[导航架构](../design/architecture/05-navigation-runtime.md)。
