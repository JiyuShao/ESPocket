# M5 — Application Ecosystem

Sequence: 005

Status: retrospective-active
Blocked by: M3 `PASS`.
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

## Further Notes

当前状态见 [M5 acceptance](../../docs/milestones/m5/acceptance.md)。长期契约见 [Runtime package trust](../../docs/design/product/05-runtime-package-trust.md)与 [App discovery](../../docs/design/product/06-application-discovery.md)。
