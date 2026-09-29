# M8 — App Interaction Contract

Sequence: 008

Status: planned
Blocked by: M7 `PASS`.

## Problem Statement

Native navigation model 必须成为 Native、Runtime 与 third-party App 共用的稳定契约，并覆盖 reclaim 与 invalid-source 行为。

## Solution

在同一产品契约下，使用真实 Native 与 Runtime App 验证 Root/Detail/Back、直接 Launch Source、Home、Screen Off、wake、reclaim 与 gesture ownership。

## User Stories

1. 作为 App author，我希望不同执行模型遵循同一交互契约。
2. 作为用户，我希望 Native 与 Runtime 的 Back/Home 行为一致。
3. 作为用户，我希望被回收 App 从 Root 重启，不恢复 stale page。
4. 作为 App，我希望普通 scroll、horizontal swipe 与 long press 得到保留。
5. 作为测试者，我希望 Native 与 Runtime 分别提供真机证据。

## Implementation Decisions

- 两种模型共享 System Core lifecycle 与产品导航语义。
- App task 保存一个直接 Launch Source。
- 需要可靠长期存在的工作归 Service 或持久化 business state。
- App 提供的 AI Native capability 遵循同一 Running Instance lifetime。

## Testing Decisions

- 要求 M7 `PASS`；M3 Runtime 证据属于依赖，不能替代本阶段证据。
- Native 与 Runtime navigation/reclaim 路径各执行 5 次。
- 使用真实 Runtime App，不使用 Native mock。

## Out of Scope

四套 template framework、任意 navigation history、后台常驻保证、low-memory killer，以及新的 Runtime 或 Shell 抽象。

## Tickets

- [01 — 完成 Native/Runtime 共享契约源码](issues/01-complete-shared-contract-source.md)
- [02 — 增加 Native 与 Runtime reclaim test seam](issues/02-add-app-reclaim-test-seams.md)
- [03 — 执行 M8 App contract hardware acceptance](issues/03-run-app-contract-hardware-acceptance.md)

## Further Notes

固定 acceptance gate 见 [M8 acceptance](../../docs/milestones/m8/acceptance.md)。
