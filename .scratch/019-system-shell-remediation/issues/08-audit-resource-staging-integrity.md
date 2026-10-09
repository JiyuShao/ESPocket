# 08 — 核查资源与构建依赖完整性

**What to build:** 核查当前产品资源及 Runtime package 的 build tree staging 和镜像依赖，发现真实缺口后在其构建 Owner 内修复。

**Blocked by:** 无；未来字体/语言/Files 新资源另依赖对应功能设计。

**Status:** resolved

- [x] 建立当前 Shell、主题、Reference Apps、Settings、Store 与 Runtime staged resources 的来源/目标/依赖矩阵。
- [x] 验证独立 clean build 使用正确资源，输入改变能更新 staging 与镜像；关键资源缺失不能以 warning 后成功替代有效产物。
- [x] staging 保持在 build tree，不污染源码树；不为尚未选择的功能提前引入资源或泛化资源管理器。
- [x] 有缺口时补齐依赖并完成相关统一检查/独立完整构建；无缺口时记录证据后关闭核查，不制造改动。
- [x] 结果写入本 Effort records，明确构建证明与尚未执行的视觉/设备路径。

## 本线隔离进展

2026-10-04：源码、工具和真实 staging/镜像实验见[隔离核查记录](../records/2026-10-04-resource-staging-tools-audit.md)。记录只属于独立源码快照；未合入原 checkout，状态和未完成验收保持开放。


2026-10-05：隔离交付已三方整合入当前 checkout；新增 Core 补丁按当前组合重新准确应用，整合中两处空 Overlay 重试回归已修复。联合 host checks、构建和设备结果见[联合整合记录](../records/2026-10-05-joint-integration.md)。此前隔离阶段记录保留；本票未满足的条件继续开放。


2026-10-09 当前核对：已整合实现、离线证据及缺代码／物理条件见[统一收尾核对](../../027-reliability-closeout/records/2026-10-09-reliability-audit.md)。历史“原 checkout 未整合”只描述当时快照，不代表当前源码。


## Resolution

当前源码中的 staging 刷新与完整性门槛已整合；025 的副本输入／完整镜像归档不再重复建设。最终统一检查与全新隔离完整构建通过，资源核查离线条件全部满足。见[027 候选证据](../../027-reliability-closeout/records/2026-10-09-unified-candidate.md)。不关闭原功能票的视觉／设备条件。
