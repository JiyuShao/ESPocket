# 06 — 采用并复验在线 Store 稳定性修复

**What to build:** 采用官方 HTTP/Store/HAL 修复，使 cancellation、timeout 与正在执行的 ESP HTTP client 操作具有正确同步，并完成非下载 Refresh 复验。

**Blocked by:** Service terminal-state/retry/timeout 回归及完整构建和设备门槛；用户已允许维护上游补丁。

**Status:** ready-for-agent

- [ ] 核对修复覆盖 retry、cancel、timeout 与活动 TLS handshake 的并发边界，并记录采用的版本或 commit。
- [ ] 锁定依赖，完成独立 clean build，记录候选镜像 identity。
- [ ] 真机执行 non-download Refresh，覆盖相关 retry/cancel 路径；记录实际结果与串口，无 panic、watchdog、assert 或自动重启。
- [ ] 分开记录 offline、cached 与 online 结果；稳定性通过前继续禁用动态安装和远程 App exposure。

## 已知失败与证据

诊断已完成不代表修复已采用。1 worker / 1 request containment 曾在 Refresh 的 retry/cancel 后发生 TLS handshake `LoadProhibited` 并重启；不继续重复已知不安全复现。

历史事实见 [Store 报告](../records/2026-09-28-acceptance-report.md)，源码诊断见 [HTTP race 草稿](../records/2026-09-28-http-cancel-race.md)及[上游状态快照](../records/2026-09-28-upstream-status.md)。这些快照不证明当前上游已经修复。

候选补丁与确定性 open/read 回归见 [2026-10-03 记录](../records/2026-10-03-http-cancel-patch.md)。尚未接入产品，不将 HAL 回归通过等同 Store 稳定性通过。

## Comments

2026-10-04：用户报告 Store 实际不可用，作为优先功能故障处理。普通 24acc698e 的缓存启动实际捕获 4 次 HTTP 容量拒绝；部分 metadata 成功，不能归为全部网络请求失败。当前 1 worker / 1 request 与 Store 图标／metadata 调度需真实回归；HAL cooperative cancel 已在 production，在线手动 Refresh 等门槛仍未通过。详见[可用性诊断](../records/2026-10-04-store-availability.md)。

2026-10-04 用户授权解决全链路：先补充[图标容量回归](../records/2026-10-04-store-icon-admission.md)，原版真实控制流失败，候选延后重试通过；完整网络与安装条件仍分别由本票及 03/08 持有。

2026-10-04：普通候选 5bb555ca5 已通过实际 online Refresh、Home 和重进，cached/online 证据分开记录；另修复合成 release 被 App launch 重新取消的输入边界，原失败 attempt 保留。见[候选构建与结果](../records/2026-10-04-store-icon-admission.md#候选构建与真实在线结果)。活动请求取消、完整 shutdown/offline 等门槛仍独立核查，未关闭本票。
