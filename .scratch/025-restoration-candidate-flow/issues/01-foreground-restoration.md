# 01 — 前台恢复投影

**What to build:** 在 System Owner 内集中启动返回 Surface、息屏目标与 Quick Settings 的显示返回投影。

**Blocked by:** None.

**Status:** resolved

## Acceptance

- [x] Core 真实运行状态和实例代次共同决定有效性，不增加生命周期管理器或重新启动 App。
- [x] 同实例恢复、同 ID 新实例拒绝、无效 Core 状态、Home/reset 清理和跨 App 启动目标回归通过。
- [x] 实际 Display 原子注册身份校验和 System QS 路由回归通过。
- [x] 统一 host checks 和完整隔离构建通过。

## Comments

真机覆盖、PWR 与视觉验收沿用 [024 呈现票](../../024-shell-overlay-presentation/issues/01-overlay-presentation.md)，本票只交付架构实现与离线回归。

## Resolution

实现、统一 host 回归与全新隔离完整构建通过。[结果与候选 identity](../records/2026-10-08-offline-verification.md)。没有执行刷机或真机验收。
