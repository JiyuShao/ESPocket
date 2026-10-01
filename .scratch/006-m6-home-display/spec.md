# Home and Display State

Sequence: 006

Status: resolved
Blocked by: [002/02 Home 与 cleanup](../002-m2-native-app/issues/02-close-the-home-and-cleanup-loop.md)（已完成）。

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
- [03 — 完成 Home 与显示真机验收](issues/03-run-hardware-acceptance.md)

## 已接受结果

2026-10-02 完成。四条固定路径各 5/5、四项单次检查和 failure scan 均通过；资源趋势无持续下降，诊断后恢复普通镜像并由用户确认。详细步骤、判定和各记录链接由 [03](issues/03-run-hardware-acceptance.md) 持有。离线 Store 缺少可见提示弹窗属于历史已知限制；在线稳定性与设备能力剩余票仍保持开放，不受本 Effort 完成影响。

## 记录

- [2026-09-29-native-detail-followup](records/2026-09-29-native-detail-followup.md)
- [2026-09-29-quick-device-smoke](records/2026-09-29-quick-device-smoke.md)
- [2026-10-01-cold-boot](records/2026-10-01-cold-boot.md)
- [2026-10-01-one-pass-checks](records/2026-10-01-one-pass-checks.md)
- [2026-10-01-pwr-sequence-followup](records/2026-10-01-pwr-sequence-followup.md)
- [2026-10-01-reclaim-test-image](records/2026-10-01-reclaim-test-image.md)
- [2026-10-01-store-failure-rescan](records/2026-10-01-store-failure-rescan.md)
- [2026-10-02-resource-trend](records/2026-10-02-resource-trend.md)
