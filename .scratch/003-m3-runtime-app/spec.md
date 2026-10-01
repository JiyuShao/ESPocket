# Runtime App Validation

Sequence: 003

Status: retrospective-resolved
Blocked by: [002/03 Native lifecycle 与 heap](../002-m2-native-app/issues/03-run-lifecycle-heap-gate.md)（已完成）。
Historical basis: 2026-09-29 重建；对独立 Core file-install 证据的已接受例外保持原义。

## Problem Statement

ESPocket 需要证明官方 packaged Runtime 能与 Native App 共存，同时不引入私有 package format、Runtime 或产品 lifecycle。

## Solution

使用官方 JavaScript Runtime、Toolkit 与 System Core staging path 构建并运行最小 Hello Runtime，使其遵循与 Hello Native 相同的 Launcher、Home 与 cleanup 契约。

## User Stories

1. 作为 App author，我希望使用官方 Toolkit 构建最小 JavaScript App。
2. 作为用户，我希望 Native 与 Runtime App 行为一致。
3. 作为 maintainer，我希望 Runtime dependency 与 package identity 锁定且可复现。
4. 作为测试者，我希望获得 clean boot discovery 与真机 Runtime lifecycle 证据。
5. 作为 release owner，我希望 unsigned debug output 与可信 release package 明确区分。

## Implementation Decisions

- 只启用官方 JavaScript Runtime 与 QuickJS backend。
- 使用官方 staging helper 与现有 LittleFS App root。
- 保持稳定 package identity `espocket.app.hello_runtime`。
- Native 与 Runtime 保留不同加载路径，共享 System Core lifecycle。
- Signing 与 remote distribution 归 [Application Ecosystem](../005-m5-application-ecosystem/spec.md) 处理。

## Testing Decisions

- 验证 dependency lock、linker retention、staging tree、LittleFS image 与 Toolkit output。
- 验证 package structure、CRC、manifest 与 JavaScript identity。
- 验证 Runtime visibility、render、Home stop 和 `Runtime → Native → Runtime` 共存。
- 将 stack-size recovery canary 保留为历史记录。

## Out of Scope

Remote Store trust、signed release publication、其他 Runtime language 与独立 Runtime 产品导航。

## Tickets

- [01 — 构建并 stage Hello Runtime](issues/01-build-and-stage-runtime-package.md)
- [02 — 证明 Runtime lifecycle 与 Native 共存](issues/02-prove-runtime-lifecycle-coexistence.md)
- [03 — 稳定 shared worker baseline](issues/03-stabilize-shared-workers.md)

## 已接受结果

| Gate | Accepted result |
|---|---|
| Runtime integration | Runtime JS 0.8.3 与 QuickJS-NG 0.14.0 解析、锁定并保留在 link map |
| Package staging | 官方 helper 将 `espocket.app.hello_runtime` staging 到 Core App root 与 LittleFS image |
| Toolkit | Toolkit 1.0.1 doctor/debug build 和 `.bpk` CRC/内容检查通过 |
| Clean discovery | clean image 启动时发现并安装 Hello Runtime |
| Physical lifecycle | Runtime 可见、渲染、启动、Home 停止与 Launcher 恢复通过 |
| Coexistence | `Runtime → Native → Runtime` 及各自 start/stop 配对通过 |
| Recovery baseline | System/Service worker stack canary 最终形成稳定配置和 clean physical pass |

Debug `.bpk` 明确未签名。项目所有者接受缺少独立 Core file-install 原始日志，不代表远程发布、签名或 M5 信任门通过。

## 记录

- [2026-09-28-acceptance-report](records/2026-09-28-acceptance-report.md)
