# Home Space gesture hardware prototype

Sequence: 011

Status: active
Blocked by: None；样机观察不自动关闭正式导航验收 ticket。

## Problem Statement

现有 Launcher 是固定双列按钮，进入后不能靠反方向上下滑回表盘。需要在真机验证纵向列表与“到顶后下拉松手返回”的手感、提示和误触边界。

## Solution

制作可回退的固件交互样机：Launcher 纵向滚动；Quick Settings 向上滑回表盘；Launcher 到顶后继续下拉超过阈值，松手回表盘；周边页有轻微返回方向提示；移除 Shell 常驻顶部状态栏。保留 PWR 语义。App Card 契约仅写入目标设计，不在本次实现。

## User Stories

1. 用户从表盘上滑进入 Launcher，能滚动列表，滑到顶部再下拉会看到反馈，松手回表盘。
2. 用户从表盘下滑进入 Quick Settings，再上滑回表盘。
3. 用户进入左右 Card，能看到轻微的返回方向提示，反向横滑回表盘。
4. 用户打开 App 后，Shell 常驻状态栏不遮挡 App。

## Implementation Decisions

- 样机只改 ESPocket 自有组件，不改 Brookesia managed components。
- Launcher 返回必须在释放时提交；过阈值的触摸不再触发 App 按钮。
- 当前固定 Card 不接入未来 App Card 机制。

## Testing Decisions

- 固件构建成功，真机上检查导航、列表滚动、返回阈值、按钮误触、PWR 与息屏恢复。
- 记录固件 identity 和人工观察；样机结论不自动关闭 007/03 的正式导航检查。

## Out of Scope

- App Card 注册、动态配置与生命周期实现。
- 通用 Launcher 动态应用发现。
- 007/03 的正式导航验收。

## Tickets

- [01 — 构建并验证 Home Space 真机交互样机](issues/01-prototype-home-space-gestures.md)

## Further Notes

参见 [交互模型](../../docs/design/product/03-interaction-model.md)、[App Card ADR](../../docs/adr/0010-app-cards-are-app-surfaces-in-home-space.md) 和 [系统导航验收](../007-m7-navigation/issues/03-run-navigation-hardware-acceptance.md)。

## 记录

- [2026-09-30-home-space-prototype](records/2026-09-30-home-space-prototype.md)
