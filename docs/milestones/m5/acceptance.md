# M5 — Application Ecosystem acceptance

> 文档类型：阶段判定与证据索引。详细历史叙述见 [`records/`](records/2026-09-28-acceptance-report.md)。

## 判定

- Status: `BLOCKED`
- Dependency: M3 `PASS`; M4 may remain blocked for independent gates
- Online Store stability: device-failed
- Remote Runtime distribution: fail closed

## 已接受

| Gate | Result |
|---|---|
| Official Store integration | Store 0.8.2、HTTP 0.8.2、TLS policy、resources 和 clean build 通过 |
| Offline lifecycle | clean image Store startup/Home 与 cached 1/1 containment lifecycle 通过 |
| Network transfer | 远程 index 和部分 metadata 曾成功写入 cache |
| Containment image | 1 worker / 1 request app-only write、hash、90-second boot、Wi-Fi 与 SNTP 通过 |
| Static analysis | 包信任、catalog compatibility 与 Runtime keyboard isolation 缺口已经识别 |

## 失败与阻塞

| Gate | Status | Evidence or requirement |
|---|---|---|
| Online Store stability | `FAIL` | 1/1 explicit Refresh 在 retry/cancel 后 `LoadProhibited` 并重启；栈位于 TLS handshake |
| Runtime package trust | `BLOCKED` | Core 必须执行统一信任门、事务激活和可信重启发现 |
| Compatible package route | `BLOCKED` | 需要 `espocket` compatible signed release 与发布/update 路径 |
| Runtime keyboard isolation | `BLOCKED` | Core 必须 owner-scope keyboard result 或保证 stop-failure cleanup |
| Dynamic Launcher | `BLOCKED` | 先通过 trust 和 online stability，再实现并真机验证 Core projection |
| Package lifecycle | `NOT TESTED` | 当前没有兼容、可信、稳定的 Store flow |

## 验收记录

- [2026-09-28 acceptance report](records/2026-09-28-acceptance-report.md) 保存完整 Store、HTTP、包安全和分发矩阵。
- [HTTP race upstream draft](../../upstream/issues/http-cancel-race.md) 和 [upstream status](../../upstream/status-2026-09-28.md)保存上游事实。
- [Runtime 包信任契约](../../design/product/05-runtime-package-trust.md)与 [App 发现契约](../../design/product/06-application-discovery.md)保存长期产品规则。

## 下一判定

采用官方 HTTP cancellation 修复并重验 non-download Refresh；取得兼容签名包；由 Core 执行信任门和 owner-scoped Runtime cleanup；最后验证动态 Launcher 和完整 package lifecycle。在这些门槛完成前保持 `BLOCKED`。
