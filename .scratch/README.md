# Local work index

`.scratch/` 是任务、依赖、状态、验收结果与历史证据的唯一工作入口。每个 Effort 使用一个 Spec、按 Sequence 排列的 tickets 和可选 records；具体规则见 [issue tracker 指南](../docs/agents/issue-tracker.md)。

## Effort registry

| Sequence | Effort | 来源 |
|---:|---|---|
| 001 | [ESPocket System](001-m1-system/spec.md) | 已接受 System 工作回填 |
| 002 | [Native App Validation](002-m2-native-app/spec.md) | 已接受 Native 工作回填 |
| 003 | [Runtime App Validation](003-m3-runtime-app/spec.md) | 已接受 Runtime 工作回填 |
| 004 | [Device Capabilities](004-m4-device-capabilities/spec.md) | 设备能力工作回填 |
| 005 | [Application Ecosystem](005-m5-application-ecosystem/spec.md) | 应用生态工作回填 |
| 006 | [Home and Display State](006-m6-home-display/spec.md) | Home 与显示状态工作 |
| 007 | [Navigation Surfaces](007-m7-navigation/spec.md) | 系统导航工作 |
| 008 | [App Interaction Contract](008-m8-app-contract/spec.md) | Native/Runtime App 交互工作 |
| 009 | [AI Native foundation](009-ai-native-foundation/spec.md) | 既有 AI Native 设计 Effort |
| 010 | [文档重组](010-docs-reorganization/spec.md) | 文档迁移与工作入口整理 |
| 011 | [Home Space gesture hardware prototype](011-home-space-gesture-prototype/spec.md) | 2026-09-30 用户确认的交互样机 |
| 012 | [真机交互自动化开发契约](012-test-automation-contract/spec.md) | 2026-09-30 用户要求定义所有权、协议与 API |
| 013 | [Firmware structure refactor](013-firmware-structure-refactor/spec.md) | 2026-10-01 用户确认的结构整理 |
| 014 | [App Page、Card 与 Back 开发契约](014-app-navigation-card-contract/spec.md) | 2026-10-01 用户确认的导航开发契约 |
| 015 | [测试目录与设备测试职责重构](015-test-layout-refactor/spec.md) | 用户确认测试分层设计后要求整体实施 |
| 016 | [上游文档与兼容目录整理](016-upstream-maintenance-layout/spec.md) | 用户确认 compat 与 patches 分开并要求整理 upstream |

## 当前工作入口

- 系统导航源码与真机验收：[007](007-m7-navigation/spec.md)。
- Navigator、Back、Native/Runtime 绑定及 Card 实现：[014](014-app-navigation-card-contract/spec.md)。
- Native/Runtime 回收与共同交互验收：[008](008-m8-app-contract/spec.md)。
- 设备能力剩余发布条件：[004](004-m4-device-capabilities/spec.md)。
- Store、包信任、Runtime isolation 与分发发布条件：[005](005-m5-application-ecosystem/spec.md)。
- 测试自动化、结构整理和 AI Native 分别见 012、013、009 的 Spec 与依赖。

本页提供入口，不复制 Spec/ticket 的状态。迁移与去重结果见 [010/08](010-docs-reorganization/issues/08-unify-task-acceptance-records.md)。

## 分配与推进

- Effort 首次登记时获得三位全局 Sequence；目录格式为 `<Sequence>-<slug>`。Sequence 不重排、不复用，标题变化时保留。
- 001–008 的目录保留历史名称中的 m1–m8，以保持路径及来源可追溯；这些编号不再定义阶段或状态。
- Spec 定义范围、整体状态和完成条件；ticket 定义执行内容、依赖和验收。records 保存有日期的历史事实，不决定当前状态。
- 新 Effort 通过 `scripts/tracker/new-effort.py` 分配 Sequence。已完成与 wontfix 的工作继续保留。
- 在一个 Effort 内，选择编号最小、依赖已全部解决且为 `ready-for-agent` 或 `ready-for-human` 的 ticket。跨 Effort 依赖优先于编号；外部 blocker 未解除时不能自动推进。
