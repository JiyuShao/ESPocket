# M7 — Navigation Surfaces

Sequence: 007

Status: planned
Blocked by: M6 `PASS` for stage acceptance.

## Problem Statement

M6 建立 Home 与 Display State 后，ESPocket 需要一套以手表为中心、贯穿 Cards、Quick Settings、Launcher 与 Native App 的导航闭环。

## Solution

实现真实 Surface content、Edge Back 与一个直接 Launch Source，同时保留 App horizontal gesture，并让 PWR Home 到达 Watch Face。

## User Stories

1. 作为用户，我希望 Watch Face 两侧具有稳定、不循环的 Cards 边界。
2. 作为用户，我希望 Quick Settings 改变真实设备状态。
3. 作为用户，我希望 Back 返回直接启动 App 的 Surface。
4. 作为 App，我希望普通 horizontal swipe 不被误判为 Edge Back。
5. 作为测试者，我希望 brightness 与 Wi-Fi 变化在真机上得到证明。

## Implementation Decisions

- Cards 保持 single-page content，不变成 nested App。
- 只保存一个直接 Launch Source；来源失效时回退到 Watch Face。
- Battery、Brightness、Wi-Fi 与 Settings 提供最小真实内容。
- Brightness 使用当前选中的真实 Display output，不使用固定 ID。

## Testing Decisions

- M6 `PASS` 是阶段 acceptance 的 gate。
- 在真机上验证完整导航闭环与每条 edge path。
- 证明真实 Wi-Fi 与 brightness 变化，不能只观察控件文案。

## Out of Scope

Runtime App 契约验证、通用 Card SDK、Card editor、任意 App-to-App history 与 dynamic Launcher。

## Tickets

- [01 — 修复 brightness output identity](issues/01-fix-brightness-output-identity.md)
- [02 — 关闭 M7 source 与 build gate](issues/02-close-navigation-source-gates.md)
- [03 — 执行 M7 navigation hardware acceptance](issues/03-run-navigation-hardware-acceptance.md)

## Further Notes

固定 acceptance gate 见 [M7 acceptance](../../docs/milestones/m7/acceptance.md)。
