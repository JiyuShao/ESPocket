# ADR-0005: Launcher projects Core-committed App state

- Status: `accepted`
- Recorded: 2026-09-29
- Origin: 从既有 Launcher sync 设计中提取；首次决策日期未知

## Context

Catalog entry、下载请求、文件系统残留和安装事件，都不能证明 Core 已提交一个可启动 App。独立 Launcher 数据库会制造另一个安装事实源。

## Decision

`Core::list_apps()` 是 dynamic Launcher entry 的权威实时来源。Shell 维护确定性的显示投影，并使用完整 Core snapshot 进行 reconciliation。固定产品 entry 保持显式且独立。

## Consequences

- Event 可以把投影标为 dirty，但不能改变安装事实。
- Refresh 失败时保留上一份完整 view。
- Manifest identity 保持稳定；runtime `AppId` 在 dispatch 时解析。
- Package trust 与在线稳定性允许 exposure 前，dynamic entry 保持隐藏。

## Alternatives rejected

- 将 Store Catalog 作为 installed-App 数据库。
- 由 Shell 扫描目录。
- 持久化 Launcher index。
- 将增量 event state 作为唯一事实源。

参见 [App 发现契约](../design/product/06-application-discovery.md)和 [应用生态任务与结果](../../.scratch/005-m5-application-ecosystem/spec.md)。
