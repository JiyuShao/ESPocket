# 前台恢复投影与隔离构建候选流程

Sequence: 025
Status: resolved
Blocked by: None.

## Problem Statement

前台恢复目标分散在 System 的启动、显示、PWR 和生命周期处理内；仅用 App ID 或局部 token 判断容易把同一 App 的新实例当作旧实例。独立构建虽已应用锁定补丁，但候选镜像与输入证明依赖手工归档，遗漏 flash_args 引用的模型等镜像，也不能证明构建副本未漂移。

## Solution

集中 System Owner 内的 Foreground Restoration Projection；每次恢复重新读取 Core 的真实运行状态与 Running Instance 身份。深化现有隔离构建入口，自动验证实际副本输入并归档完整 Build Candidate。

## User Stories

1. 打开并关闭 Quick Settings 后，仍有效的同一次 App 实例保持原页面和显示来源；失效目标不能恢复。
2. 构建者可以从一个候选目录核查全部刷写镜像、源码 inventory、补丁、配置与 lock 的身份。

## Implementation Decisions

- Core 继续拥有生命周期；System 投影只保存恢复意图与实例身份，不创建第二份 App 状态，不启动 App。
- App ID + 单次启动代次共同标识前台 Running Instance；有效性依赖 Core active、Running、visible 与 System 已提交身份匹配。
- 显示来源注册 identity 的最终原子校验继续留在 Display Owner。
- 复用 build_patched_firmware.py；stage 保存实际副本的不可变输入，构建期间不以变化中的 checkout 充当编译输入证明。
- 原始 managed_components 不修改，保留现有 ADR-0016 精确源码/补丁校验。成功构建且复核后才发布 candidate；失败保留证据。
- LittleFS 候选是全新文件系统产物，已有设备替换继续使用独立备份与迁移流程。

## Testing Decisions

- 编译实际投影 interface 和 Core 状态采样方法；验证旧实例、无效状态、不同 App 的启动目标、Home/reset 撤销。
- 实际 System QS 处理和 Display guard 回归继续验证重新注册与选择竞态。
- 隔离构建测试覆盖完整产物、输入漂移、缺失镜像、路径越界、prepare-only 与构建失败。
- 统一 host checks、Markdown 和全新隔离 ESP-IDF 完整构建必须通过。
- 真机交互与时延继续由前置验收票持有，不将离线通过写为设备通过。

## Out of Scope

刷机、串口测试、提交/push、Core 新状态机、普通讲话全双工打断、AEC 声学验收及启动阶段性能优化。

## Tickets

1. [前台恢复投影](issues/01-foreground-restoration.md)
2. [隔离构建候选](issues/02-build-candidate.md)

## Further Notes

遵循 [ADR-0016](../../docs/adr/0016-maintained-upstream-fixes.md) 和 [覆盖请求归属](../../docs/adr/0017-overlay-arbitration-preserves-request-ownership.md)。真机覆盖条件继续由 [024 呈现票](../024-shell-overlay-presentation/issues/01-overlay-presentation.md)持有。

[离线验证与候选证据](records/2026-10-08-offline-verification.md)。
