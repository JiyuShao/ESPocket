# 01 — 旧票核对与离线可靠性

**What to build:** 核对旧票与现有实现，修复真实 stop 请求失效缺口。

**Blocked by:** None.

**Status:** resolved

## Acceptance

- [x] 017、019/01–05、08 与 024–026 的重叠和缺项有源码／测试依据。
- [x] Core stop 残留系统 Dialog 请求、调度拒绝后重启／迟到键盘结果均有实际生产方法红灯复现及修复。
- [x] 失败清理、停止、迟到回调、Card 更新／回滚与资源 staging 的 host 回归通过。
- [x] 统一检查和完整隔离构建通过，旧票当前状态与证据更新。

## Comments

本票不关闭真机条件；正常停止清理不宣称 GUI 锁失败、scheduler rejection 或完整产品重复运行已全部验收。

## Resolution

已完成旧票核对、必要的 Core 请求失效修复、统一检查和完整隔离构建。见[核对记录](../records/2026-10-09-reliability-audit.md)。
