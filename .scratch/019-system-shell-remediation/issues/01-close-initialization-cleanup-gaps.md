# 01 — 修复初始化与失败清理

**What to build:** 在 System、Display、Core 和 Native Shell 的真实 Owner 内补齐失败路径获得/释放关系，实现 OVR-011 的可诊断关键失败。

**Blocked by:** [018/01 审计与设计确认](../../018-system-super-reference-audit/issues/01-audit-system-and-shell.md)（已完成）。

**Status:** ready-for-agent

- [ ] 核对补丁后的实际控制流，覆盖 source.start 后角色选择失败、Core partial init 和 Native Shell start 失败，不直接把原 managed source 当生产行为。
- [ ] 逐失败点验证已有资源被回收，不双重释放；仍可用显示提供错误信息，不能显示时保留诊断；恢复方式为显式重启。
- [ ] 验证 callback 停止、GUI 锁/调度失败与清理结果；不能仅因业务 on_stop 成功就宣称全部回收。
- [ ] 框架修复遵守 ADR-0016，独立副本、精确版本/hash、补丁回归和移除条件完整。
- [ ] 统一检查、独立完整构建和关键失败后的真机诊断/显式重启路径分别记录；资源结果由真实 Owner 的可观察证据支持。

## Execution Notes

先复现审计矩阵中的具体失败边界，再修复；不创建统一 rollback manager。正常重复运行归 02，失败后的同对象重试不在本票承诺内。证据写本 Effort records，链接 [审计事实](../../018-system-super-reference-audit/records/2026-10-04-system-shell-audit.md)。

## Isolated Candidate

2026-10-04：本线在隔离副本实施并验证源码候选，详见[候选记录](../records/2026-10-04-isolated-lifecycle-candidate.md)。状态和未勾选门槛保留；原 checkout 未整合、设备未操作，不以 host 结果代替 callback/视觉/真机重复生命周期证据。


2026-10-05：隔离交付已三方整合入当前 checkout；新增 Core 补丁按当前组合重新准确应用，整合中两处空 Overlay 重试回归已修复。联合 host checks、构建和设备结果见[联合整合记录](../records/2026-10-05-joint-integration.md)。此前隔离阶段记录保留；本票未满足的条件继续开放。
