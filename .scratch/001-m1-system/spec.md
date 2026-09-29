# M1 — ESPocket System

Sequence: 001

Status: retrospective-resolved
Blocked by: None.
Historical basis: 2026-09-29 根据已接受的 M1 记录重建；证据未包含的 Sequence、owner 与时间保持未知。

## Problem Statement

ESPocket 需要一套可复现的产品 System：通过 Brookesia 启动 Waveshare 目标板、呈现可用的 Circular Shell、保留可诊断失败，同时不演变成 framework fork。

## Solution

基于锁定的 Brookesia 公开 seam 组合 ESPocket System，生成 board configuration，以确定顺序启动必需 Service 和隐藏 Shell App；只有 clean build 与真机稳定性 gate 都通过后才接受 baseline。

## User Stories

1. 作为设备用户，我希望产品启动到可用系统 UI，使设备具有稳定起点。
2. 作为 maintainer，我希望从声明的依赖完成 clean build，使本地生成状态不进入 baseline。
3. 作为调试者，我希望致命启动失败停止并留下串口证据，使故障可诊断。
4. 作为产品开发者，我希望 ESPocket 复用 Brookesia manager，避免产品工作形成 framework fork。
5. 作为 release owner，我希望执行重复冷启动和软件复位，避免一次成功启动被当成 baseline。

## Implementation Decisions

- ESPocket System 是 Brookesia System Core 之上的产品 composition root。
- Circular Shell 使用隐藏 Native App carrier，不出现在普通 App 列表中。
- Display、Touch、System Core 与 Shell 启动失败属于 fatal；状态类 capability 可以降级。
- Platform Baseline 包含 ESP-IDF 版本、已解析 component lock 与 board selector。
- M0 保持 waived，不回填为通过。

## Testing Decisions

- 在不使用生成目录的情况下复现构建。
- 在真机上验证 display、touch、Launcher 与 Home 行为。
- 要求 5 次冷启动和 10 次 EN/software reset 全程无 fatal signal。
- 在历史记录中保留准确的 image 与 memory 观察。

## Out of Scope

Native App 验证、Runtime package、设备 capability、Store distribution，以及后续 Watch Face Home 模型。

## Tickets

- [01 — 复现 Platform Baseline](issues/01-reproduce-platform-baseline.md)
- [02 — 通过 System Core 启动 Circular Shell](issues/02-boot-circular-shell.md)
- [03 — 证明 baseline 启动稳定性](issues/03-prove-boot-stability.md)

## Further Notes

历史判定与证据索引见 [M1 acceptance](../../docs/milestones/m1/acceptance.md)。
