# Shell Overlay 呈现集中与真实 interface 回归

Sequence: 024

Status: blocked
Blocked by: 真机覆盖恢复与触摸验收待设备返回

## Problem Statement

Quick Settings、Dialog 与 Keyboard 的覆盖、清理和结果交付顺序分散于绘制、导航与 timer；测试抽取多个源码片段并重声明 Shell，缺少真实 module interface 的连续场景验证。用户选择架构候选 01，并确认范围、验收重点及最终方案。

## Solution

在现有 CircularShell 私有 implementation 内集中 Shell Overlay 呈现规则，复用既有 interface 与 Core request identity；不新增请求队列或第二个 lifecycle Owner。

## User Stories

1. 收起 Quick Settings 后恢复有效的最高优先级提示；有效键盘保留原草稿。
2. 覆盖期间 Dialog 自动关闭计时继续，失效请求不得恢复或晚交付。
3. PWR 先丢弃未提交选择；GUI 清理失败重试，成功后仅交付一次。

## Implementation Decisions

- 优先级与现有视觉不变：Quick Settings、Dialog、Keyboard、Loading。
- 绘制保留各自 implementation，建立对象时先隐藏，由集中呈现逻辑统一显示；移除 Dialog 到 Keyboard 的直接控制与公开 suspend helper。
- Core 保留请求身份、有效性与结果裁决；Shell 保留 Dialog 自动关闭的呈现计时。Quick Settings 覆盖不停计时，息屏暂停呈现计时。前置讨论把全部“期限”归 Core 的表述过宽，本票明确该差别。
- GUI lock 先于 state mutex；Core 查询和结果回调都在这些锁外执行。
- 呈现稳定时不反复获取 GUI 锁；协调失败时不交付尚未确认可操作的选择。

## Testing Decisions

- 完整编译实际 CircularShell 声明、状态、呈现与绘制源码；host fixture 仅替换 boot/status 及外围集成，不重声明 Shell 或抽取源码。
- 连续验证覆盖过期、草稿恢复、撤销、PWR、锁失败重试、身份隔离、更新失败、息屏计时与 QS transition 失败。
- 运行 firmware host checks、Markdown 与隔离完整构建；fake LVGL 不替代物理触摸与帧输出证据。

## Out of Scope

- 不改 App/Core 请求生命周期，不迁移 Dialog 呈现计时，不新增通用 Overlay manager。
- 不处理单阶段启动阻塞，不宣称 250ms 已满足。
- 不连接或部署设备，不提交或 push 当前批次。

## Tickets

- [01 — 呈现 implementation 与真实 interface 回归](issues/01-overlay-presentation.md)

## Further Notes

- [2026-10-08 离线结果](records/2026-10-08-offline-presentation.md)

- [Overlay Owner 决策](../../docs/adr/0017-overlay-arbitration-preserves-request-ownership.md)
