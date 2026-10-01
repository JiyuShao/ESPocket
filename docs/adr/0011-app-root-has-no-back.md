# ADR-0011: App Root 不提供 Back

- Status: `accepted`
- Recorded: 2026-10-01
- Origin: 用户确认 ESPocket 的 App Root 返回行为与 Apple Watch 一致，并完成 Home Space、App Card、Back 和自动化开发契约访谈

## Context

[ADR-0002](0002-watch-face-is-the-only-home.md) 与 [ADR-0010](0010-app-cards-are-app-surfaces-in-home-space.md) 曾要求 Root Back 恢复启动 App 的 Card 或 Launcher。这使 App 根页面具有与子页面相同的返回入口，也让 App 内导航依赖一个 Shell 来源。用户选择让 App Root 成为不可 Back 的导航起点；PWR Home 仍可随时到达 Watch Face。

## Decision

Watch Face 继续是唯一 Home。App 声明唯一 Root 和稳定的 Page 类型 ID；App 决定页面转移，ESPocket 保存 App 内导航栈并统一处理 Back。Root 没有可见默认 Back，也不响应 Edge Back；子页面 Back 返回栈中上一页面。App 可以暂缓普通 Back 以确认未保存内容，但不能阻止 PWR Home。

App Card 仍是同一 App 在 Home Space 的专门呈现形态。Card 可打开 App Root 或声明的目标 Page；目标 Page 的栈以 Root 为底。离开 App 的系统入口是 PWR Home，直接返回 Watch Face，不恢复启动来源。首版不提供跨 App 返回链。

## Consequences

- 既有 Root Back → Launch Source 的产品要求、验收门槛和实现都需要替换；既往构建与静态结果不能证明新规则已经实现。
- ESPocket 需要为 Native 与 Runtime App 提供相同的 Page 声明、导航栈、Back 分发和快照语义，而不是要求 App 自行维护并回报第二份栈。
- Card 的配置位置和 App 的页面栈保持分离；息屏唤醒可以恢复有效页面，PWR 离开后再次打开 App 从 Root 开始。

## Alternatives rejected

- 保留 Root Back 返回 Card 或 Launcher：这把 App 的退出和 App 内层级返回混成同一操作。
- 由 App 各自维护整条页面栈并向 ESPocket 回报当前页面：默认 Back 和自动化快照容易与真实页面状态分叉。
