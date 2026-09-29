# M2 — Native App Validation acceptance

> 文档类型：阶段判定与证据索引。详细历史叙述见 [`records/`](records/2026-09-26-acceptance-report.md)。

## 判定

- Status: `PASS`
- Date: 2026-09-26
- Dependency: M1 `PASS`

## 固定门槛

| Gate | Accepted result |
|---|---|
| Native lifecycle | `Hello Native` 完成 install、discover、start、Running、Action、stop、Stopped 和 Launcher restore |
| Stable identity | Manifest ID `espocket.app.hello` 用于发现，运行期 `AppId` 在 Core 中解析 |
| Physical path | Launcher → Hello → Increment → Home → Launcher 通过 |
| Stress | 50/50 lifecycle cycles 通过；四项 heap loss 均为 0，低于 1,024-byte gate |
| Cleanup | GUI unload probe、Shell callback cleanup 和 App resource ownership 通过 |
| Build | 最终 normal/stress 镜像和 LittleFS image 构建并烧录验证；早期镜像明确 superseded |

## 验收记录

- [2026-09-26 acceptance report](records/2026-09-26-acceptance-report.md) 保存镜像 identity、生命周期设计、物理检查和复现命令。

## 历史边界

本页不把后来加入的 Runtime、Settings 或 Shell Surface 行为回写为 M2 交付。对应 `.scratch` Spec/tickets 是回顾性重建。
