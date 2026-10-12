# 05 — 实施保存主题临时回退

**What to build:** 实现 OVR-013、OVR-015，保存主题未知或 apply 失败时本次回默认并保留原偏好；默认不可用走关键启动失败。

**Blocked by:** [01 关键失败清理](01-close-initialization-cleanup-gaps.md)。

**Status:** ready-for-agent

- [x] 主题在 App/Surface 资源使用前选择；未知 ID 与 apply 失败均有默认回退和原因诊断。
- [x] 临时回退不改写保存值；重启保留原偏好，用户明确选择可用主题时才更新偏好。
- [x] 默认主题不可用按关键失败清理并等待显式重启；不继续运行部分主题界面。
- [ ] 回归覆盖上述分支和持久化结果；统一检查、独立完整构建与默认回退的真机视觉/重启证据通过。

## Execution Notes

资源配色迁移仍归 [017](../../017-theme-token-migration/spec.md)。本票不交付即时切换；其行为由 10 单独设计。

## Isolated Candidate

2026-10-04：本线在隔离副本实施并验证源码候选，详见[候选记录](../records/2026-10-04-isolated-lifecycle-candidate.md)。状态和未勾选门槛保留；原 checkout 未整合、设备未操作，不以 host 结果代替 callback/视觉/真机重复生命周期证据。


2026-10-05：隔离交付已三方整合入当前 checkout；新增 Core 补丁按当前组合重新准确应用，整合中两处空 Overlay 重试回归已修复。联合 host checks、构建和设备结果见[联合整合记录](../records/2026-10-05-joint-integration.md)。此前隔离阶段记录保留；本票未满足的条件继续开放。


2026-10-09 当前核对：已整合实现、离线证据及缺代码／物理条件见[统一收尾核对](../../027-reliability-closeout/records/2026-10-09-reliability-audit.md)。历史“原 checkout 未整合”只描述当时快照，不代表当前源码。

当前有效主题的保存／恢复可在普通候选验收；unknown/apply-failure 与默认不可用的实际故障路径缺测试夹具，不能把整票只归为等待设备。

2026-10-12：新增隔离构建专用的[可靠性测试入口](../../../firmware/test/device/fixtures/reliability/README.md)，注入先于输入冻结。产品初始化关键资源边界、三轮外部生命周期协调及主题回退故障已有执行入口；不修改 NVS 偏好。未访问设备，完整 Core 分配点/GUI 锁/真实 callback 竞争矩阵仍开放，不据入口存在勾选真机条件。

新增入口的完整构建、九模式目标编译与未验边界见 [2026-10-12 离线证据](../records/2026-10-12-offline-reliability-fixtures.md)。
