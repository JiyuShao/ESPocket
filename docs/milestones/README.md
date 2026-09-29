# ESPocket Milestones

本页是阶段状态的唯一摘要。每个 `acceptance.md` 定义固定门槛、执行步骤和当前判定；`records/` 保存可读历史与关键验收事实。

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

## 验收记录规则

- `records/` 必须保存日期、状态、镜像 identity、关键测量值、失败、豁免和未验证项。
- 原始构建日志、串口日志和中间诊断输出不进入源码树；需要短期共享时使用 CI 或 Release artifact。
- 删除临时日志前，必须把影响判定的事实提炼到对应 record。
- `records/` 中的叙述可以重组，但已接受的事实和判定不得改写。
- Host build、Preview 或静态检查不能替代明确要求的物理显示、触控、PWR 或串口证据。
- 上游修复只有经过本项目独立构建和硬件验收后才改变 Milestone 状态。

具体真机步骤和固定重复次数由对应阶段的 acceptance 定义。实施计划、提出顺序与可执行工作见 [Local work index](../../.scratch/README.md)。
