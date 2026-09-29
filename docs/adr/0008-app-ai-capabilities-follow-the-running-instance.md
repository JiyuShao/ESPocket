# ADR-0008: App AI capabilities follow the Running Instance

- Status: `accepted`
- Recorded: 2026-09-29
- Origin: 从既有 AI Native 设计中提取；首次决策日期未知

## Context

App 可能停止、崩溃、重启或被回收。让 Context、Action 或 Event handle 超过该实例继续存活，会留下 stale object，并与 System Core lifecycle 事实冲突。

## Decision

Native App 或 Runtime App 注册的 capability 属于一个 Running Instance。实例结束时，其 handle 与 subscription 全部失效。新启动获得新 identity 和新 registration。需要跨越 App lifetime 的 capability 归 Brookesia Service 持有。

## Consequences

- Assistant 必须启动已停止的 App，或使用持久 Service。
- Native 与 Runtime cleanup 遵循同一语义规则。
- AI Native 不延长 App lifetime，也不创建第二套 App 状态机。

## Alternatives rejected

- 永久全局注册 App 持有的 object。
- 跨 App 重启复用 handle。
- 仅为保留 AI access 而让 App 常驻。

参见 [App 生命周期架构](../design/architecture/04-boot-lifecycle.md)和 [AI Native 架构](../design/architecture/07-ai-native.md)。
