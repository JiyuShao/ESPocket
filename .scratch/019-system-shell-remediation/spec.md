# System 与 CircularShell 整改及 Super 功能对齐路线图

Sequence: 019

Status: active
Blocked by: 无全局阻塞；实施与设计前置见各 ticket。

## Problem Statement

System Super 参考审计确认了 ESPocket 现有路径的生命周期、输入竞争与失败恢复缺口，也发现状态表达、资源完整性及条件性扩展的后续工作。需要把已定行为、待设计功能和既有生态任务分开持有，形成可执行且不重复建设的路线图。

## Solution

先完成现有路径可靠性，再分批对齐固定版 Super 已实际接通的功能；生态闭环按既有任务依赖推进。已有等价能力保留，缺项按上游完整功能范围制定迁移与验收计划，不再默认裁剪成只读 Files 或仅电脑诊断。适配继续使用真实 Owner 和锁定版 Brookesia seam，保留 Circular Shell、Watch Face、PWR 与已经确认的产品契约。

## 路线图与归属

| 范围 | 工作入口 | 前置与边界 |
|---|---|---|
| 首批：现有路径可靠性 | 本 Effort 01–05 | 失败清理、全量 stop/正常重复、Overlay、Loading/PWR、主题回退；行为已定，设备证据待实施 |
| 第二批：状态与维护 | 本 Effort 06–08 | 对齐真实状态与设备调试链路，完成兼容设计；资源完整性可独立核查；callback 停止安全属于首批验收 |
| 第三批：生态闭环 | [005](../005-m5-application-ecosystem/spec.md)与 [014/03](../014-app-navigation-card-contract/issues/03-card-registry-lifecycle.md)、[014/05](../014-app-navigation-card-contract/issues/05-card-samples-api-finalization.md) | trust、Store、签名发布的实际依赖继续有效；动态 Launcher 与 replacement/Card 迁移不另开同义票 |
| Super 能力对齐 | 本 Effort 09–12、15 | 语言/字体、即时主题、完整 Files、显示源恢复和扩展提示均纳入目标；条件能力按真实硬件/API 启用，分批交付 |
| 可并行工具 | 本 Effort 13 | 构建分析、编译策略与 Profiler 查询先核实收益和开销 |
| 手机配网产品入口 | 本 Effort 14 | 复用已有 Wi-Fi Service；入口、恢复和退出规则先完成设计 |
| Assistant | [009](../009-ai-native-foundation/spec.md)，Agent Manager / XiaoZhi 单列在 [009/08](../009-ai-native-foundation/issues/08-connect-a-voice-provider.md) | 使用共同 Owner、输入与生命周期基础；不在本 Effort 新增 Provider 或权限系统 |

批次表示优先级，不构成额外阻塞边；执行顺序以每张 ticket 的 Blocked by 为准。

## Super 功能对齐清单

对齐基线为官方提交 `e937455b0db1a3e873b1da61d6d13652f3dcc7e2` 的实际执行路径。每项记录现有等价能力、迁移差异与验证证据；完整范围不表示一次性导入全部依赖。

| 上游已接通能力 | 计划归属 | 对齐方式 |
|---|---|---|
| System/Shell 生命周期、App 安装/启动/停止与恢复 | 01–02、既有 Core/App 工作 | 保留同一 Owner；Home 使用已确认的 Watch Face |
| 动态 Launcher、图标/资源回退 | 005/04、08 | 保留现有 Core 投影设计，补资源与布局差异 |
| Startup overlay、Shell 启动动画、App Loading | 03–04、08 | 迁移真实 Shell 呈现链路，适配圆屏及 PWR 响应 |
| Keyboard、MessageDialog、系统提示 | 03 | 保留已有能力与请求身份，补跨类仲裁和退出规则 |
| Wi-Fi/时钟/时区、状态栏展开与 App 内临时显示 | 06 | 按上游功能核对，再适配已有 Quick Settings 和圆屏导航 |
| Light/Dark 恢复与即时刷新、语言/字体预载与回退 | 05、09–10 | 保留已完成主题变量成果，补上游运行时与字体链路 |
| Settings、Store、Files | 11、既有 004/005 | Settings/Store 已接入；Files 包含卷/目录浏览、容量/信息、重命名、删除与确认流程 |
| Settings → Utils Memory/Thread Debug → Shell overlay | 07、13 | 保留完整设备调试链路；构建支持、开发模式和共享采集生命周期需适配 |
| 非 GUI Display source 与临时系统 GUI 的切换/恢复 | 12 | 对齐已有路由逻辑；真实 source 可用时启用，不由依赖推断视频/NES 已可用 |
| Expansion 模块状态/插拔提示 | 15 | 仅真实 ModuleManagerIface 可用时订阅与呈现 |
| 资源 staging、构建分析和编译工具 | 08、13 | 沿现有构建 Owner 提取适用能力并验证工具链兼容 |

固定 Super 的 Notifications 入口实际转到 Launcher，Quick Control/System Monitor 返回停用错误，不存在对应完整页面可迁移。手机 SoftAP 配网来自独立 Wi-Fi/Chatbot 示例，归 14；Agent Manager / XiaoZhi 继续在 009/08 单列。完整事实与源码锚点见[本轮记录](records/2026-10-04-service-app-extension-plan.md#super-实际接通功能基线)。

## User Stories

1. 作为用户，我在启动等待、输入重叠和系统停止时仍能得到确定的 Home 与失败恢复结果。
2. 作为维护者，我能区分已确认行为、待选择功能和已经有效的历史证据。
3. 作为实施 Agent，我能从具体 ticket 找到 Owner、依赖、验证范围和完成边界。

## Implementation Decisions

- [018](../018-system-super-reference-audit/spec.md) Q4–Q14 的已接受行为由产品与架构文档持有；Q16 确认完整后续工作范围。
- stop 与 deinit、呈现计时与执行期限、待提交与已提交结果保持不同语义。
- Native 与 Runtime 使用同一产品契约；正常重复生命周期不包含关键启动失败后的原地重试承诺。
- Shell 不复制 Core 请求队列、App registry 或 Service 状态事实；补丁按 ADR-0016 在真实 Owner 内维护。
- 已完成 [005/07](../005-m5-application-ecosystem/issues/07-isolate-runtime-keyboard-results.md)的 Runtime 隔离证据继续有效，新票只持有新的行为与回归条件。
- 用户最新方向将 Super 实际接通功能作为默认对齐目标。06–07、09–12、15 的兼容设计与验收仍需完成，但不再逐项询问是否保留上游已有功能；017 的主题变量迁移不等于即时主题切换。
- 仅在上游行为与现有已接受契约冲突、真实硬件不支持或公开接口不足时列出具体差异；需要改变既有决定时显式重新打开，不把技术事实交给用户猜测。

## Testing Decisions

- 当前建立路线图只运行 Markdown 文档检查，不执行固件实施或设备操作。
- 实施修改按仓库规则运行统一 host checks；必要完整构建与新增真机条件在各票记录，源码、构建与设备结果分开判定。
- 对失败清理和竞争行为使用真实控制流或 Owner seam 的回归；不以 UI 存在、日志成功或单次重启替代验收。
- 250 ms 是 PWR 短按识别至 Watch Face 的后续目标，当前没有测量证据。
- 既有通用导航/App 交互证据继续由 007、008、014 持有，不在本 Effort 重复建立整套验收。

## Out of Scope

依赖自动升级、第二套生命周期/Installer/权限系统、既有生态与 Assistant 票的重复实现；迁移目标不包括固定 Super 未接通的产品入口。当前只完善计划，不提前安装新组件或宣称硬件/真机兼容已通过。

## Tickets

- [01 — 修复初始化与失败清理](issues/01-close-initialization-cleanup-gaps.md)
- [02 — 完成全量停机与正常重复生命周期](issues/02-complete-stop-and-normal-restart.md)
- [03 — 实施 Overlay 输入与期限规则](issues/03-arbitrate-overlay-input-and-deadlines.md)
- [04 — 增加 Loading 并验证启动期间 PWR](issues/04-add-loading-and-responsive-startup.md)
- [05 — 实施保存主题临时回退](issues/05-fallback-unavailable-saved-theme.md)
- [06 — 设计现有状态的有效性与呈现](issues/06-design-status-validity-and-presentation.md)
- [07 — 对齐 Super 设备调试链路](issues/07-design-development-diagnostics.md)
- [08 — 核查资源与构建依赖完整性](issues/08-audit-resource-staging-integrity.md)
- [09 — 设计中文与多语言支持](issues/09-design-language-and-font-support.md)
- [10 — 设计即时主题切换](issues/10-design-live-theme-switching.md)
- [11 — 对齐完整 Files 功能](issues/11-design-files-integration.md)
- [12 — 设计非 GUI 显示源支持](issues/12-design-non-gui-display-sources.md)
- [13 — 评估构建与 Profiler 工具](issues/13-evaluate-build-and-profiler-tools.md)
- [14 — 设计手机 Wi-Fi 配网入口](issues/14-design-phone-wifi-provisioning.md)
- [15 — 对齐条件性扩展模块提示](issues/15-design-expansion-notifications.md)

## Further Notes

- [审计事实矩阵](../018-system-super-reference-audit/records/2026-10-04-system-shell-audit.md)
- [访谈决定与范围确认](../018-system-super-reference-audit/records/2026-10-04-audit-decisions.md)
- [Service 与 App 补充迁移核查](../018-system-super-reference-audit/records/2026-10-04-service-app-migration-review.md)：区分现有票、可复用模式与尚未接受的新功能候选。
- [产品总览](../../docs/design/product/01-overview.md)、[系统交互](../../docs/design/product/03-interaction-model.md)、[启动与生命周期](../../docs/design/architecture/04-boot-lifecycle.md)
- [ADR-0016 维护补丁](../../docs/adr/0016-maintained-upstream-fixes.md)、[ADR-0017 Overlay 所有权](../../docs/adr/0017-overlay-arbitration-preserves-request-ownership.md)
- [Files、手机配网与诊断计划访谈](records/2026-10-04-service-app-extension-plan.md)

## Comments

2026-10-04：用户再次调用 grill-with-docs，要求 Agent Manager / XiaoZhi 单列、完善其余计划。本轮深入 07 诊断、11 Files 与新增 14 手机配网的产品规则；保持此前首批整改与其它票归属。active 表示计划访谈正在进行，本轮不执行固件实施、构建或设备操作。

2026-10-04：用户进一步提出「Super 实现了啥全部搬过来」。计划改为默认对齐固定 Super 的实际完整功能，撤回 Q17–Q20 对 Files/诊断的缩减式选择，补全启动动画、显示源恢复与条件性扩展提示的归属。该方向不等于所有兼容设计已经完成；当前仍是计划与源码核查。

2026-10-04：用户授权独立推进 01/02/05，本线实施位于仓库外 baseline/working 快照；[生命周期候选记录](records/2026-10-04-isolated-lifecycle-candidate.md)区分源码、构建与设备结果。既有 Store 与 Overlay/Loading 线不重复，原 checkout 不修改，相关 tickets 尚未关闭。


2026-10-04 隔离线完成 06/07/09/10/11/12/14/15 的源码兼容核查和执行单元草案，形成[记录](records/2026-10-04-compatibility-design.md)、[产品范围](../../docs/design/product/08-system-capability-alignment.md)、[Owner 视图](../../docs/design/architecture/06-device-capabilities.md#能力-owner-与-adapter)和[目标 seam](../../docs/development/system-capability-seams.md)。真实待选规则精确列于记录；这些设计票未 resolved，也未宣称新增源码、独立固件构建或设备验收完成。原 checkout 与当前 Store/可靠性施工不由本线修改。

2026-10-04：用户授权独立推进 03/04，本线只在 baseline/working 快照实施。03 增加真实 Core 请求查询与 Shell 输入/呈现仲裁回归；04 兼容 Loading seam 已准备，同步启动/PWR、Super 自有启动动画与设备门槛仍未完成。01/02/05、Store 与 009 的归属及依赖未改变，原 checkout 未整合。见[隔离实施记录](records/2026-10-04-overlay-isolated-implementation.md)。


2026-10-05：四线交付已三方整合入当前 checkout，保留原包性能修改；源码、联合验证与仍未完成的门槛见[联合整合记录](records/2026-10-05-joint-integration.md)。Super 部分为兼容设计成果，未把未选择规则当成已接受或已实现。
