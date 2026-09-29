# ESPocket Milestones

本目录保存阶段规范与验收结果。已完成阶段记录实际结果；未开始阶段记录进入条件和固定验收门槛。

## 状态总览

| 阶段 | 状态 | 文档 | 下一条件 |
|---|---|---|---|
| M0 Official Baseline | `WAIVED` | [M0 豁免决策](#m0-official-baseline-waiver) | 无；不得改写为 `PASS` |
| M1 ESPocket System | `PASS` | [M1 验收](m1-acceptance.md) | 已完成并标记 `v0.1-system` |
| M2 Native App Validation | `PASS` | [M2 验收](m2-acceptance.md) | 已完成 |
| M3 Runtime App Validation | `PASS` | [M3 验收](m3-acceptance.md) | 已完成；独立 Core `.bpk` file-install 门槛由项目所有者接受 |
| M4 Device Capabilities | `BLOCKED` | [M4 验收](m4-acceptance.md) | 补齐设备检查并等待 playback-only 上游修复 |
| M5 Application Ecosystem | `BLOCKED` | [M5 验收](m5-acceptance.md) | 解决 HTTP race、trust gate、兼容包与发布路径 |
| M6 Home & Display State | `IN PROGRESS` | [M6 验收](m6-acceptance.md) | 实现并完成真机验收 |
| M7 Navigation Surfaces | `NOT ENTERED` | [M7 规范](m7-acceptance.md) | M6 通过 |
| M8 App Interaction Contract | `NOT ENTERED` | [M8 规范](m8-acceptance.md) | Native 依赖 M7；Runtime 验证另依赖 M3 |

## M0 Official Baseline waiver

- 状态：`WAIVED`
- 日期：2026-09-25
- 决策：项目所有者选择直接进入 M1。
- 影响：官方基线风险被接受，并在 M1 中暴露和处理；M0 不得标记为 `PASS`。

## 证据组织

原始证据位于 [`evidence/`](evidence/README.md)，按验证对象分组：

- `m2/`：Native lifecycle stress。
- `m3-m5/`：Runtime、Settings、Store 共用的启动、内存和交互证据。
- `m4/`：键盘、Wi-Fi 与设备能力证据。
- `m5/`：在线 Store、HTTP containment 与崩溃诊断证据。
- `m6/`：Home、PWR 与显示状态的主机侧实现证据。
- `m7-m8/`：导航 Surface、App 交互契约与 clean build 证据。

跨阶段证据只保留一份，并由所有相关验收文档链接到同一路径。
