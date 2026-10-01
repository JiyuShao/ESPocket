# Native App Validation

Sequence: 002

Status: retrospective-resolved
Blocked by: [001/03 System 启动稳定性](../001-m1-system/issues/03-prove-boot-stability.md)（已完成）。
Historical basis: 2026-09-29 根据已接受的 M2 证据重建；不声称这些 tickets 在实现期间已经存在。

## Problem Statement

M1 shell baseline 尚未证明真实可见的 Native App 能通过 System Core 重复完成安装、启动、更新、停止与清理。

## Solution

增加一个最小 Hello Native tracer bullet，覆盖安装、Launcher discovery、GUI Action、Home stop、Shell restoration，以及 50 轮真机 lifecycle/heap gate。

## User Stories

1. 作为用户，我希望从 Launcher 启动可见 App，并可靠返回 Home。
2. 作为 App author，我希望 manifest identity 稳定，并使用普通 AppContext GUI 行为。
3. 作为平台 maintainer，我希望 Core 持有 App lifecycle 与 cleanup。
4. 作为测试者，我希望获得可重复的 lifecycle 证据和可测量 heap gate。
5. 作为调试者，我希望 superseded image 有明确标识，避免误刷。

## Implementation Decisions

- Hello Native 是最小真实产品 App，使用稳定 manifest identity。
- System Core 解析 runtime App identity，并持有 start/stop state。
- Home intent 在 Core App task 中消费，不从 display callback 调用 lifecycle code。
- Shell 与 status callback 具有明确 cleanup ownership。
- 普通构建中禁用 stress runner。

## Testing Decisions

- 测试完整 Launcher → Hello → Increment → Home → Launcher 路径。
- 要求 50 轮成功，并具有明确 Running/Stopped 与 GUI unload probe。
- 比较早期与后期 heap median，loss gate 为 1,024 bytes。
- Cleanup warning、reset 与 malformed evidence protocol 均视为失败。

## Out of Scope

Runtime App、dynamic installation、Settings、Store 和通用 App template。

## Tickets

- [01 — 交付可见 Native App tracer bullet](issues/01-native-app-tracer-bullet.md)
- [02 — 闭合 Home 与 cleanup loop](issues/02-close-the-home-and-cleanup-loop.md)
- [03 — 执行 Native lifecycle 与 heap gate](issues/03-run-lifecycle-heap-gate.md)

## 已接受结果

| Gate | Accepted result |
|---|---|
| Native lifecycle | `Hello Native` 完成 install、discover、start、Running、Action、stop、Stopped 和 Launcher restore |
| Stable identity | Manifest ID `espocket.app.hello` 用于发现，运行期 `AppId` 在 Core 中解析 |
| Physical path | Launcher → Hello → Increment → Home → Launcher 通过 |
| Stress | 50/50 lifecycle cycles 通过；四项 heap loss 均为 0，低于 1,024-byte gate |
| Cleanup | GUI unload probe、Shell callback cleanup 和 App resource ownership 通过 |
| Build | 最终 normal/stress 镜像和 LittleFS image 构建并烧录验证；早期镜像明确 superseded |

本页不把后来加入的 Runtime、Settings 或 Shell Surface 行为回写为 M2 交付。对应 `.scratch` Spec/tickets 是回顾性重建。

## 记录

- [2026-09-26-acceptance-report](records/2026-09-26-acceptance-report.md)
