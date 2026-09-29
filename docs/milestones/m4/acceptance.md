# M4 — Device Capabilities acceptance

> 文档类型：阶段判定与证据索引。详细历史叙述见 [`records/`](records/2026-09-28-acceptance-report.md)。

## 判定

- Status: `BLOCKED`
- Dependency: M3 `PASS`
- Accepted work remains valid; open gates below prevent `PASS`.

## 已接受

| Gate | Result |
|---|---|
| Official Settings integration | Settings 0.8.3 与 Audio service 0.8.2 解析、构建和 staging 通过 |
| Hardware UI | Settings 466×466 smoke、Wi-Fi、Brightness、Time、Battery、Device info 与 Home 通过 |
| Keyboard | Host build、一次 matching open/close 与项目所有者确认的屏上语义通过 |
| Wi-Fi/SNTP | 10 个静态 RX buffer、保留 NVS reconnect 与 SNTP 同步有脱敏真机证据 |
| Framework boundary | 未复制 Settings/Audio framework，未修改 `managed_components/` |

## 未通过门槛

| Gate | Status | Required evidence |
|---|---|---|
| Storage visibility | `NOT TESTED` | 真机读取与 UI 行为 |
| Developer controls | `NOT TESTED` | 真机控制和返回路径 |
| Sound/Volume | `BLOCKED` | 官方 playback-only `PlaybackIface` 路径，Codec Recorder 保持关闭 |

## 证据索引

- [2026-09-28 acceptance report](records/2026-09-28-acceptance-report.md) 保存完整依赖、构建、设备矩阵和阻塞分析。
- [M4 raw evidence](../evidence/m4/) 保存键盘、Wi-Fi 和设备记录。
- [Upstream status](../../upstream/status-2026-09-28.md) 保存 Audio playback-only 版本事实。

## 下一判定

完成 Storage/Developer 真机检查并采用官方 Audio 修复后，重新执行相关 clean build 与硬件门槛；在此之前保持 `BLOCKED`。
