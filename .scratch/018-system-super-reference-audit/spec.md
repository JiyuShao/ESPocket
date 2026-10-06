# System 与 CircularShell 参考审计

Sequence: 018

Status: resolved
Blocked by: 无。

## Problem Statement

对照官方 System Super，完整检查 ESPocket System 与 CircularShell 的职责、生命周期和产品行为，区分已有覆盖、真实缺口、待验证项与产品选择差异，避免按上游文件或功能数量直接决定迁移。

## Solution

形成源码差异矩阵、需要确认的产品决定和后续工作建议。以本项目 glossary、已接受 ADR 和产品契约为约束；上游作为固定版本参考。审计目标、证据范围和实施顺序通过 grill-with-docs 逐轮收敛。

## User Stories

1. 作为项目维护者，我希望知道哪些 System/Shell 行为已由本项目或 Core 持有，避免重复建设。
2. 作为产品设计者，我希望以具体用户路径判断差异，并明确需要补充什么证据。

## Implementation Decisions

- 2026-10-04 用户选择完整系统审计，范围包括启动/退出、App 集成和恢复、Overlay/输入、状态、主题/字体与资源。
- 本轮为调查与设计讨论；未确认的建议不作为已接受架构决定，不实施固件迁移。
- 上游参考固定为 ESP-Brookesia `e937455b0db1a3e873b1da61d6d13652f3dcc7e2`，不隐式升级产品锁定依赖。
- 用户确认审计排序优先体验与可靠性；功能扩展、维护与开发效率仍在覆盖范围内。
- Q4–Q10 已确认：关键启动失败回收资源并保持可诊断状态，由显式重启恢复；stop 停止所有受管 App/产品入口，deinit 释放资源；Dialog 优先于 keyboard，Loading 最低；键盘期间 Back 取消输入且不导航底层页面；PWR 优先于待提交结果；系统提示可留在 Home，息屏暂停呈现自动关闭计时但不延长操作/授权/Owner 期限；保存主题不可用回默认主题；首批只完善现有路径可靠性。
- Q11–Q14 已确认：Loading 覆盖启动等待与 App 主动等待请求，具体任务行为留在 Owner；有效 PWR 短按识别后 250 ms 内返回 Watch Face 为后续验证目标；同一 System 对象支持正常 stop→start 与 deinit→init；主题临时回退保留保存值，用户选择时更新偏好。
- 已接受行为由 [产品总览](../../docs/design/product/01-overview.md)、[交互模型](../../docs/design/product/03-interaction-model.md) 持有；生命周期结构由 [启动与生命周期](../../docs/design/architecture/04-boot-lifecycle.md) 持有；Overlay 所有权见 [ADR-0017](../../docs/adr/0017-overlay-arbitration-preserves-request-ownership.md)。文档描述目标，不宣称固件已实现。
- Q15 用户确认已收敛的首批理解，并要求补充后续整改范围；候选路线图见访谈记录，不将新建议自动记为已接受产品要求。
- Q16 用户确认完整后续范围：现有状态与维护能力、生态闭环、独立功能扩展和工具工作纳入路线图。具体实施、未定产品行为与验收由 [019 整改路线图](../019-system-shell-remediation/spec.md)及既有生态、Assistant tickets 持有。

## Testing Decisions

- 修改文档后执行 `python3 scripts/docs/check.py --markdown`。
- 源码调查与历史验收分开陈述；新增验证场景由后续实施票定义。
- 用户确认本轮只使用源码与已有证据，输出后续必测场景；不新增主机回归、固件构建或设备操作。

## Out of Scope

当前不执行固件改动、依赖升级、烧录或真机操作。Assistant Provider 集成和包信任任务继续由既有 Effort 持有；本审计可引用其前置，不重复分配。

## Tickets

- [01 — 完成系统差异审计与设计访谈](issues/01-audit-system-and-shell.md)

## Further Notes

- [既有 examples 调查](../009-ai-native-foundation/records/2026-10-04-brookesia-examples-review.md)
- [核心 Module 架构](../../docs/design/architecture/03-core-modules.md)
- [ADR index](../../docs/adr/README.md)
- [2026-10-04 初步差异矩阵](records/2026-10-04-system-shell-audit.md)
- [2026-10-04 访谈决定与审计交付](records/2026-10-04-audit-decisions.md)
- [2026-10-04 Service 与 App 补充核查](records/2026-10-04-service-app-migration-review.md)：后续调查，不将候选记为已实现或自动扩大原审计实施范围。

## Resolution

用户已确认首批行为与完整后续范围，审计设计树收敛。差异矩阵、已接受产品/架构规则、ADR 和后续工作入口已交付。本 Effort 只关闭调查与设计访谈；整改实现、构建和设备验收未在本轮执行，由 019 或既有 tickets 分别持有。
