# Application Ecosystem

Sequence: 005

Status: retrospective-active
Blocked by: [003/02 Runtime lifecycle 与共存](../003-m3-runtime-app/issues/02-prove-runtime-lifecycle-coexistence.md)（已完成）；上游及分发依赖见各 ticket。
Historical basis: 2026-09-29 根据已接受 Store 工作、真机失败和未解决 distribution gate 重建。

## Problem Statement

ESPocket 需要官方 Store 与远程 Runtime distribution path，但锁定的上游栈尚未提供稳定 cancellation、统一 package trust boundary、兼容 signed package 或可信 dynamic Launcher source。

## Solution

保留官方 Store 与 Service；当前在线路径不稳定时 fail closed；要求 Core 持有 trust gate；只有安全与稳定性 gate 通过后，Launcher 才投影 Core committed state。

## User Stories

1. 作为用户，我希望 Store browse 与 refresh 不导致设备崩溃或重启。
2. 作为用户，我希望下载的 App 在可执行前完成验证。
3. 作为 maintainer，我希望 Core 持有唯一 installation truth。
4. 作为 Launcher，我希望只显示可信且已提交的 App。
5. 作为 Runtime App 用户，我希望 keyboard 与 Service result 隔离到对应 owner App。
6. 作为 release owner，我希望获得可审计 signed package 与兼容 publication path。

## Implementation Decisions

- 使用官方 Store、HTTP、Storage、Runtime 与 System Core path。
- 1/1 cancellation failure 完成 symbolization 后，online Store 保持 blocked。
- 在 Core 公开 install boundary 执行 Runtime trust contract。
- Dynamic Launcher projection 使用完整 Core snapshot。
- 所有前置 gate 通过前，dynamic installation 与 exposure 保持禁用。

## Testing Decisions

- 分别保留 offline、cached 与 online Store 结果。
- 不为增加一次样本而重复已知不安全 crash。
- 进入 package lifecycle 前，先使用 non-download Refresh 重新验证官方 HTTP fix。
- 端到端测试 verification、transaction rollback、reboot discovery、update、uninstall 与 Launcher reconciliation。
- 上游源码事实与产品 acceptance 分开记录。

## Out of Scope

私有 Store backend、私有 downloader、私有 package format、产品自有 Installer，以及把 debug 或 build-staged package 当作 remote release 信任。

## Tickets

- [01 — 集成官方 Store](issues/01-integrate-official-store.md)
- [02 — 诊断 online Store failure](issues/02-diagnose-online-store-failure.md)
- [03 — 执行 Core 持有的 package trust gate](issues/03-enforce-core-package-trust.md)
- [04 — 从 Core 投影 dynamic Launcher entry](issues/04-project-dynamic-launcher-from-core.md)
- [05 — 验证 remote package lifecycle](issues/05-validate-package-lifecycle.md)
- [06 — 采用并复验在线 Store 修复](issues/06-adopt-online-store-stability-fix.md)
- [07 — 隔离 Runtime keyboard result](issues/07-isolate-runtime-keyboard-results.md)
- [08 — 取得兼容签名包与发布路径](issues/08-publish-compatible-signed-package.md)

## Further Notes

长期规则见 [Runtime package trust](../../docs/design/product/05-runtime-package-trust.md)与 [App discovery](../../docs/design/product/06-application-discovery.md)。

## 已接受结果

| Gate | Result |
|---|---|
| Official Store integration | Store 0.8.2、HTTP 0.8.2、TLS policy、resources 和 clean build 通过 |
| Offline lifecycle | clean image Store startup/Home 与 cached 1/1 containment lifecycle 通过 |
| Network transfer | 远程 index 和部分 metadata 曾成功写入 cache |
| Containment image | 1 worker / 1 request app-only write、hash、90-second boot、Wi-Fi 与 SNTP 通过 |
| Static analysis | 包信任、catalog compatibility 与 Runtime keyboard isolation 缺口已经识别 |

## 剩余工作与完成条件

在线稳定性由 [06](issues/06-adopt-online-store-stability-fix.md) 关闭；包信任由 [03](issues/03-enforce-core-package-trust.md) 关闭；Runtime isolation 由 [07](issues/07-isolate-runtime-keyboard-results.md) 关闭；兼容签名包与发布路径由 [08](issues/08-publish-compatible-signed-package.md) 关闭。前置条件成立后，再完成 [04 动态 Launcher](issues/04-project-dynamic-launcher-from-core.md) 和 [05 包生命周期](issues/05-validate-package-lifecycle.md)。这些未完成项仍是当前产品范围内的发布条件。

## 记录

- [2026-09-28-acceptance-report](records/2026-09-28-acceptance-report.md)

## 当前功能优先级

2026-10-04 用户明确 Store 不能稳定请求或安装，先推进 06 的实际 HTTP／Store 调度回归，再解除 08、03 的兼容包和统一信任事务前置。页面打开、缓存列表和 Home 正常不构成 Store 可用；[当前诊断](records/2026-10-04-store-availability.md)记录普通设备的容量拒绝与包不兼容。07 键盘隔离已通过独立门槛，不再作为尚未完成的隔离项。
