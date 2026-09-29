# ESPocket Milestones

本页是阶段状态的唯一摘要。每个 `acceptance.md` 定义固定门槛和当前判定；`records/` 保存可读历史，`evidence/` 保存不可变原始证据。

## 当前状态

| Stage | Status | Acceptance | Next gate |
|---|---|---|---|
| M0 Official Baseline | `WAIVED` | [waiver](#m0-official-baseline-waiver) | 永远不改写为 `PASS` |
| M1 ESPocket System | `PASS` | [M1](m1/acceptance.md) | completed; `v0.1-system` |
| M2 Native App Validation | `PASS` | [M2](m2/acceptance.md) | completed |
| M3 Runtime App Validation | `PASS` | [M3](m3/acceptance.md) | completed; file-install evidence exception accepted |
| M4 Device Capabilities | `BLOCKED` | [M4](m4/acceptance.md) | Storage/Developer hardware checks and official playback-only Audio path |
| M5 Application Ecosystem | `BLOCKED` | [M5](m5/acceptance.md) | HTTP fix, trust gate, compatible release and dynamic Launcher path |
| M6 Home & Display State | `IN PROGRESS` | [M6](m6/acceptance.md) | hardware acceptance |
| M7 Navigation Surfaces | `NOT ENTERED` | [M7](m7/acceptance.md) | M6 `PASS`; brightness OutputId path remains open |
| M8 App Interaction Contract | `NOT ENTERED` | [M8](m8/acceptance.md) | M7 `PASS` and M8 Native/Runtime hardware evidence |

## M0 Official Baseline waiver

- Status: `WAIVED`
- Date: 2026-09-25
- Decision: 项目所有者选择直接进入 M1。
- Historical effect: 官方基线风险由项目接受并在后续集成中处理；缺少当时替代方案比较，因此不回填 ADR。

## 证据规则

- 原始记录位于 [`evidence/`](evidence/README.md)，可以被多个阶段引用，但只保存一份。
- 已被 acceptance 引用的证据文件不原地改写；修订使用新文件并记录替代关系。
- `records/` 中的叙述可以重组，日期、状态、结果、失败、豁免、未验证项和 evidence identity 不得改变。
- Host build、Preview 或静态检查不能替代明确要求的物理显示、触控、PWR 或串口证据。
- 上游修复只有经过本项目独立构建和硬件验收后才改变 Milestone 状态。

真机执行流程见[硬件验收指南](../guides/hardware-acceptance.md)。实施计划、提出顺序与可执行工作见 [Local work index](../../.scratch/README.md)。
