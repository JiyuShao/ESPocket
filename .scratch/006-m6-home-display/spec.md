# M6 — Home and Display State

Sequence: 006

Status: resolved
Blocked by: M2 `PASS`.

## Problem Statement

ESPocket 必须用完整的 Watch Face Home、PWR 与 Screen Off 状态模型取代 Launcher-as-home 行为，并在目标设备上完成验证。

## Solution

使用 Watch Face 作为 Home；让 PWR short press 经过已定义的 Home/Off/Wake 状态机；保持 Display State 与导航正交；resume target 失效时安全回退。

## User Stories

1. 作为用户，我希望每次启动与 Home 操作都到达 Watch Face。
2. 作为用户，我希望 PWR 根据可见状态分别表示 Home、Off 或 Wake。
3. 作为用户，我希望 wake 恢复有效 App 页面，不虚构已经丢失的状态。
4. 作为用户，我希望无效 resume target 回退到 Watch Face。
5. 作为测试者，我希望测试具有固定重复次数和真机证据。

## Implementation Decisions

- Home、Back 与 Display State 保持独立。
- PWR long press 继续由硬件持有；BOOT 保持 reserved。
- Screen Off 忽略 touch，不改变导航。
- Reclaim fallback 可以使用聚焦 test seam，不提前创建通用 memory manager。

## Testing Decisions

- 四条固定真机路径各执行 5 次。
- 覆盖 Overlay、touch-while-off、BOOT、long-press 与 fatal-signal 检查。
- 串口证据必须配合屏幕与按键的物理观察。

## Out of Scope

Cards、Quick Settings、Edge Back、dynamic Launcher 与任意后台调度。

## Tickets

- [01 — 实现 Watch Face Home 与 Display State](issues/01-implement-home-display-state.md)
- [02 — 增加可控 reclaim fallback seam](issues/02-add-reclaim-fallback-seam.md)
- [03 — 执行 M6 hardware acceptance](issues/03-run-hardware-acceptance.md)

## Further Notes

固定 acceptance gate 见 [M6 acceptance](../../docs/milestones/m6/acceptance.md)。
