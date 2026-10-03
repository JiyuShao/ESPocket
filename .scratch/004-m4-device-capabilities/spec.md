# Device Capabilities

Sequence: 004

Status: retrospective-active
Blocked by: [003/02 Runtime lifecycle 与共存](../003-m3-runtime-app/issues/02-prove-runtime-lifecycle-coexistence.md)（已完成）；剩余依赖见各 ticket。
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
- Audio 原先因官方接口不支持 playback-only composition 而 blocked；2026-10-03 根据 ADR-0016 采用受维护的 HAL 修复，实际验收见 04。默认 production 配置的合入不由候选验收自动完成。
- 获得真机检查前，Storage 与 Developer 保持开放。

## Testing Decisions

- 区分 host build/static evidence 与真机语义。
- 验证官方资源与 clean staging。
- 验证 Settings layout、capability page、keyboard behavior、Wi-Fi reconnect 与 SNTP。
- Sound/Volume 以真实播放、音量变化和退出停止验收，不以构建或 volume 日志代替听感。

## Out of Scope

私有 Settings 实现、私有 Audio framework、启用 recorder，以及对未测试 Storage/Developer 行为作出结论。

## Tickets

- [01 — 在圆形目标设备集成官方 Settings](issues/01-integrate-official-settings.md)
- [02 — 证明 keyboard、Wi-Fi 与 status capability](issues/02-prove-keyboard-wifi-and-status.md)
- [03 — 验证 Storage 与 Developer control](issues/03-verify-storage-and-developer.md)
- [04 — 采用官方 playback-only Audio path](issues/04-adopt-playback-only-audio.md)
- [05 — 修复官方 Settings 控件渲染](issues/05-fix-settings-controls-rendering.md)
- [06 — 系统确认弹窗](issues/06-support-settings-message-dialog.md)
- [07 — 修复 playback 退出时重复关闭 I2S](issues/07-fix-audio-playback-teardown.md)

## 已接受结果

| Gate | Result |
|---|---|
| Official Settings integration | Settings 0.8.3 与 Audio service 0.8.2 解析、构建和 staging 通过 |
| Hardware UI | Settings 466×466 smoke、Wi-Fi、Brightness、Time、Battery、Device info 与 Home 通过 |
| Keyboard | Host build、一次 matching open/close 与项目所有者确认的屏上语义通过 |
| Wi-Fi/SNTP | 10 个静态 RX buffer、保留 NVS reconnect 与 SNTP 同步有脱敏真机证据 |
| Framework boundary | 未复制 Settings/Audio framework，未修改 `managed_components/` |

## 剩余工作与完成条件

[04 playback-only Audio](issues/04-adopt-playback-only-audio.md) 的受维护候选验收已完成；默认 production 配置尚未合入。[03 Storage/Developer 真机检查](issues/03-verify-storage-and-developer.md) 已完成；剩余检查由 06 系统确认弹窗和 07 playback teardown 承接；不重做已经接受的 Settings、keyboard、Wi-Fi 与 status 工作。

## 记录

- [2026-09-28-acceptance-report](records/2026-09-28-acceptance-report.md)

后续实际缺陷由 06 系统确认弹窗与 07 playback teardown 承接；04 的候选物理验收已经通过，整个 Effort 仍保持开放。
