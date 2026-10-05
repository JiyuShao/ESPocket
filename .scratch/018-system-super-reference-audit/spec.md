# System 与 CircularShell 参考审计

Sequence: 018

Status: active
Blocked by: 源码矩阵已完成；Loading 范围、启动响应和重复生命周期等派生规则仍在访谈。

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
