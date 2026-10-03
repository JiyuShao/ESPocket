# ADR-0004: Core owns the Runtime package trust gate

- Status: `accepted`
- Recorded: 2026-09-29
- Origin: 从既有 package trust 设计中提取；首次决策日期未知

## Context

Runtime package 可以通过多个产品入口到达，也会在重启后被重新发现。只在 Store 或解包后验证可以被绕过，无法形成单一安装事实源。

## Decision

每个远程来源的 Runtime package 都必须在解包或激活前，通过 Core 持有的公开安装边界上的单一 fail-closed trust gate。该 gate 覆盖 artifact identity、release signature、member integrity、产品兼容性、事务式激活和可信的重启发现。

当公开 Core 边界无法执行该契约时，dynamic installation 保持禁用。ESPocket 不创建私有 Installer 绕过这一限制。

## Consequences

- Store 下载成功不等于安装成功。
- Verification 与 unpacking 使用同一份不可变输入。
- Activation 必须完整提交，或保留此前的可信版本。
- 缺少上游 seam 可以继续阻塞 application ecosystem 工作。

## Alternatives rejected

- 只在 Store 中验证。
- 在宽松的 Core path 外增加产品 wrapper。
- 安装后验证。
- 第二套 ESPocket package manager 或 Installer。

参见 [Runtime package trust 契约](../design/product/05-runtime-package-trust.md)和 [应用生态任务与结果](../../.scratch/005-m5-application-ecosystem/spec.md)。

## 开发者模式修订

[ADR-0018](0018-developer-mode-allows-unsigned-packages.md) 对发行签名要求增加用户已接受的开发者模式例外；Core 统一安装边界、事务与重启验证职责保持有效。
