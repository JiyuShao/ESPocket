# 06 — 采用并复验在线 Store 稳定性修复

**What to build:** 采用官方 HTTP/Store/HAL 修复，使 cancellation、timeout 与正在执行的 ESP HTTP client 操作具有正确同步，并完成非下载 Refresh 复验。

**Blocked by:** [02 已完成的 cancellation race 诊断](02-diagnose-online-store-failure.md)；可采用的官方修复。

**Status:** needs-info

- [ ] 核对修复覆盖 retry、cancel、timeout 与活动 TLS handshake 的并发边界，并记录采用的版本或 commit。
- [ ] 锁定依赖，完成独立 clean build，记录候选镜像 identity。
- [ ] 真机执行 non-download Refresh，覆盖相关 retry/cancel 路径；记录实际结果与串口，无 panic、watchdog、assert 或自动重启。
- [ ] 分开记录 offline、cached 与 online 结果；稳定性通过前继续禁用动态安装和远程 App exposure。

## 已知失败与证据

诊断已完成不代表修复已采用。1 worker / 1 request containment 曾在 Refresh 的 retry/cancel 后发生 TLS handshake `LoadProhibited` 并重启；不继续重复已知不安全复现。

历史事实见 [Store 报告](../records/2026-09-28-acceptance-report.md)，源码诊断见 [HTTP race 草稿](../records/2026-09-28-http-cancel-race.md)及[上游状态快照](../records/2026-09-28-upstream-status.md)。这些快照不证明当前上游已经修复。
