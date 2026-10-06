# 13 — 评估构建与 Profiler 工具

**What to build:** 单独评估官方构建分析、ccache/目标级并行策略与只读 Profiler 查询，给出可复现的采用建议。

**Blocked by:** 无；执行完整基线构建时协调当前构建/设备占用。

**Status:** ready-for-agent

- [x] 对照固定上游 analyze_build.py 与 compile_tuning.cmake，核实锁定产品工具链/Ninja 元数据兼容性。
- [x] 在同环境记录 clean/incremental 构建时间、资源开销与缓存条件；不直接复制固定并行数或放宽 warning policy。
- [ ] 核实已存在的 Profiler/Console 入口，记录可用指标、运行开销和开发模式/USB 约束。
- [x] 构建分析、编译策略、Profiler 三项分别给出收益、代价、采用/延后建议；实际采用有独立范围与验收票。
- [x] 记录命令、工具/版本和测量值，Markdown 检查通过；未测量项明确保留，工具工作不阻塞首批可靠性。

## 本线隔离进展

2026-10-04：源码、工具和真实 staging/镜像实验见[隔离核查记录](../records/2026-10-04-resource-staging-tools-audit.md)。记录只属于独立源码快照；未合入原 checkout，状态和未完成验收保持开放。


2026-10-05：隔离交付已三方整合入当前 checkout；新增 Core 补丁按当前组合重新准确应用，整合中两处空 Overlay 重试回归已修复。联合 host checks、构建和设备结果见[联合整合记录](../records/2026-10-05-joint-integration.md)。此前隔离阶段记录保留；本票未满足的条件继续开放。
