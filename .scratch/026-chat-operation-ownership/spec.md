# 聊天 App 异步操作归属

Sequence: 026
Status: resolved
Blocked by: None.

## Problem Statement

聊天 App 切换 Agent 后，旧 Activate/Start 请求的延迟失败仍可覆盖新 Agent 的状态并清除新的启动等待。发现、网络、配置与唤醒的等待状态和有效性检查分散，容易遗漏请求归属。

## Solution

在 Chat App 内集中异步操作的归属校验和 pending 状态，以当前运行身份、实际服务句柄、选定 Agent 与请求代次决定结果是否仍可发布。

## User Stories

1. 切换 Agent 或重新发起操作后，旧结果不能覆盖当前界面或清除新操作的等待状态。
2. 当前有效请求的失败仍可显示；真实 Started/Awake 事件继续确认运行状态。

## Implementation Decisions

- 用户已同意 App 内收拢 discovery/network/configure/start/wake；不增加平台模块或 Core 补丁。
- operations.js 只管理结果归属，不复制 Agent 生命周期，不取消已提交的 Brookesia 副作用。
- discovery/network 绑定实例及对应服务句柄；configure/start/wake 另绑定选定 Agent 和选择代次，覆盖 A→B→A。
- Activate 与 Start 共用一次启动归属；真实事件确认后延迟失败失效。
- 保留停止、挂起、重试和导航行为。没有请求 ID 的服务事件仍按真实 Owner 事实处理，不宣称已关联到某次请求。
- Chat 包版本更新为 0.1.6；完整构建只使用独立副本，不改原始 managed_components。

## Testing Decisions

- 实际 App 入口回归覆盖旧 Activate/Start/WakeUp 失败、同类重试、A→B→A、事件确认与当前失败。
- 实际模块 interface 回归覆盖所有操作替换、旧 finally 清理、句柄变化和实例失效。
- 统一 host checks、Markdown、包内容校验与全新隔离固件构建必须通过。
- 离线验收不代替真机声学、流畅度或唤醒验收。

## Out of Scope

部署、串口、commit/push、新 Core 状态机、AEC、普通讲话全双工打断，以及取消已提交的服务操作。

## Tickets

1. [App 异步操作归属](issues/01-chat-operation-ownership.md)

## Further Notes

真机对话、回音与唤醒沿用 [020 对话验收](../020-local-runtime-apps/issues/03-conversation-stutter-echo.md)和[硬件恢复验收](../020-local-runtime-apps/issues/04-chat-wake-hardware-reset.md)。构建遵循 [ADR-0016](../../docs/adr/0016-maintained-upstream-fixes.md)。

[离线验证证据](records/2026-10-08-offline-verification.md)。
