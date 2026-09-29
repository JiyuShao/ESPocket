# M3 — Runtime App Validation acceptance

> 文档类型：阶段判定与证据索引。详细历史叙述见 [`records/`](records/2026-09-28-acceptance-report.md)。

## 判定

- Status: `PASS`
- Date: 2026-09-28
- Dependency: M2 `PASS`
- Independent Core `.bpk` file-install evidence: `ACCEPTED BY PROJECT OWNER` without a new raw log

## 固定门槛

| Gate | Accepted result |
|---|---|
| Runtime integration | Runtime JS 0.8.3 与 QuickJS-NG 0.14.0 解析、锁定并保留在 link map |
| Package staging | 官方 helper 将 `espocket.app.hello_runtime` staging 到 Core App root 与 LittleFS image |
| Toolkit | Toolkit 1.0.1 doctor/debug build 和 `.bpk` CRC/内容检查通过 |
| Clean discovery | clean image 启动时发现并安装 Hello Runtime |
| Physical lifecycle | Runtime 可见、渲染、启动、Home 停止与 Launcher 恢复通过 |
| Coexistence | `Runtime → Native → Runtime` 及各自 start/stop 配对通过 |
| Recovery baseline | System/Service worker stack canary 最终形成稳定配置和 clean physical pass |

## 证据索引

- [2026-09-28 acceptance report](records/2026-09-28-acceptance-report.md) 保存 lock、镜像、Toolkit、包 identity、设备恢复和内存计算。
- [M3–M5 shared raw evidence](../evidence/m3-m5/) 保存 clean boot、canary 与物理生命周期记录。

## 历史边界

Debug `.bpk` 明确未签名。项目所有者接受缺少独立 Core file-install 原始日志，不代表远程发布、签名或 M5 信任门通过。
