# M4 — Device Capabilities

Sequence: 004

Status: retrospective-active
Blocked by: M3 `PASS`.
Historical basis: 2026-09-29 根据已完成工作与未关闭的 M4 gate 重建；已接受结果属于历史，未解决 gate 保持当前状态。

## Problem Statement

ESPocket 需要在圆形目标设备上提供官方 Settings 与真实设备 capability，同时不复制上游 App，也不启用超出产品边界的硬件功能。

## Solution

通过 Brookesia 集成官方 Settings 与必需 Service，提供产品 keyboard seam，验证可用硬件 capability，并让尚不受支持的 playback-only Audio 保持 fail closed。

## User Stories

1. 作为用户，我希望 Settings 页面能在圆形屏幕上正常工作。
2. 作为用户，我希望 Wi-Fi、brightness、time、battery 与 device information 反映真实状态。
3. 作为 Settings App，我希望系统 keyboard 具备正确 masking 与 completion 语义。
4. 作为 product owner，我希望提供 playback-only Audio，同时不静默启用 recording。
5. 作为测试者，我希望每项未验证 capability 都明确保持开放。

## Implementation Decisions

- 复用官方 Settings 与 Audio component，不 patch managed component。
- ESPocket System 持有 keyboard provider；Circular Shell 持有其 transient Overlay。
- Wi-Fi 初始化必须满足目标设备真实 buffer 与 NVS 行为。
- 官方接口支持 playback-only composition 前，Audio 保持 blocked。
- 获得真机检查前，Storage 与 Developer 保持开放。

## Testing Decisions

- 区分 host build/static evidence 与真机语义。
- 验证官方资源与 clean staging。
- 验证 Settings layout、capability page、keyboard behavior、Wi-Fi reconnect 与 SNTP。
- 根据 released/current upstream 的直接核查，让 Sound/Volume 保持 blocked。

## Out of Scope

私有 Settings 实现、私有 Audio framework、启用 recorder，以及对未测试 Storage/Developer 行为作出结论。

## Tickets

- [01 — 在圆形目标设备集成官方 Settings](issues/01-integrate-official-settings.md)
- [02 — 证明 keyboard、Wi-Fi 与 status capability](issues/02-prove-keyboard-wifi-and-status.md)
- [03 — 验证 Storage 与 Developer control](issues/03-verify-storage-and-developer.md)
- [04 — 采用官方 playback-only Audio path](issues/04-adopt-playback-only-audio.md)

## Further Notes

当前状态与证据索引见 [M4 acceptance](../../docs/milestones/m4/acceptance.md)。
