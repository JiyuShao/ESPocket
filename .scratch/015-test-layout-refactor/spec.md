# 测试目录与设备测试职责重构

Sequence: 015

Status: resolved
Blocked by: None — 用户已确认目录与命名方案。

## Problem Statement

设备测试的 USB 协议、断言、导航/Card 用例和 CLI 混在 interaction_driver.py；跨模块主机测试与 Runtime App 自身测试混在 firmware/test。开发者难以按 Owner 与执行环境定位测试，默认检查也未显式区分设备用例。

## Solution

按 Owner 放置局部测试，跨模块主机测试归 firmware/test/host，真实设备测试归 firmware/test/device。保留 scripts 为操作入口，设备执行器、USB 客户端与 E2E 用例分开。

## User Stories

1. 开发者能按组件或 App 找到其局部断言。
2. 无设备的主机检查不会连接串口或执行 device suites。
3. 操作者可用 run_device_tests.py 运行原导航/Card 用例，原 CLI 参数与报告语义兼容。

## Implementation Decisions

- 保留组件与 Native/Runtime App 的 test 目录；按实际职责移动 Runtime 样例测试。
- USB 协议与快照校验归 UsbTestClient；行为断言、attempt、日志尾部与清理归 DeviceTestRunner。
- navigation/cards 用例归 device/e2e；设备坐标归 device/profiles。
- 旧 CLI 保留薄转发，旧 profile 用符号链接指向唯一配置。
- 不变更固件协议、设备刺激、产品行为、重复次数或证据分类。

## Testing Decisions

- 全量 scripts/check.py；主机 discovery 显式覆盖 Runtime App 与 host，排除 device。
- CLI 仓库外调用、无设备 help、受控 transport 失败保留报告、旧入口兼容。
- 用例 AST 对比及一次新入口实际 navigation attempt。
- 本次只有测试工具与文档变化，无固件实现、资源或构建配置变化，不需重编译/刷写固件；新入口使用当前已验证普通镜像。

## Out of Scope

新增回收/稳定性套件、改动产品或测试协议、补齐其他 tickets 的物理验收、推送 Git。

## Tickets

- [01 — 调整测试目录与设备执行职责](issues/01-reorganize-tests.md)

## Resolution

目录与职责迁移完成；主机、CLI 与一次新入口设备导航检查通过，见 [实施证据](records/2026-10-02-test-layout.md)。原 CLI 保留兼容入口，无固件或协议行为变更。
