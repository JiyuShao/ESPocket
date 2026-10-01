# ADR-0002: Watch Face is the only Home

- Status: `superseded`
- Recorded: 2026-09-29
- Origin: 从既有设计中提取；首次决策日期未知

本记录由 [ADR-0011](0011-app-root-has-no-back.md) 取代；Watch Face 仍是唯一 Home，Root Back 与 Launch Source 的旧决定不再适用。

## Context

ESPocket 面向小尺寸圆形手表屏幕。手机式 Launcher Home、Home/Back 共用历史栈，以及 Screen Off 期间改变导航，都会与手表交互模型冲突并造成恢复语义不明确。

## Decision

Watch Face 是固定 Home 目标，也是 Home Space 的中心。Launcher、Quick Settings、Cards 和 App 是其他 Surface。Home、Back 与 Screen Off 各自具有独立语义。

一个 App task 只记录一个直接 Launch Source。Root Back 返回该来源；来源失效时回退到 Watch Face；产品不维护任意跨 App 历史链。

## Consequences

- PWR Home 始终到达 Watch Face，并可结束当前 navigation task。
- Screen Off 保留导航状态，唤醒时尽力恢复。
- Launcher 是 App finder，而不是系统根节点。
- 更复杂的跨 App 工作流需要显式 continuation model。

## Alternatives rejected

- 将 Launcher 作为 Home。
- 将 Home 与 Back 视为同一操作。
- 将 Screen Off 视为导航跳转。
- 在初始产品契约中维护无界的手机式 task history。

参见[交互模型](../design/product/03-interaction-model.md)和 [App 契约](../design/product/04-app-contract.md)。
