# ADR-0014: Runtime Card 首版采用声明式呈现

- Status: `accepted`
- Recorded: 2026-10-02
- Origin: 用户确认声明式 Runtime Card 首版，由 ESPocket 管理显示、刷新、暂停和打开目标 Page；独立 JS 业务回调留待上游安全实例能力

## Context

App Card 与完整 App 使用同一安装身份，但处于不同导航和可见生命周期。锁定 Runtime Manager 使用共享 backend，JS Backend 构造私有且为单例。另建 Runtime 对象不能隔离 Card，并可能在 deinit 时清理 Core 的共享 backend。Core 未提供独立 Card JS 实例的公开 Owner seam。

## Decision

首版 Runtime Card 通过版本化 cards.json 提供专用 GUI 和有限的数据绑定，不执行独立 JS 生命周期、任意业务动作或后台订阅。ESPocket 在真实安装声明中校验 Card 稳定身份，创建与挂载独立文档，管理可见、暂停、重新读取数据和释放。当前数据绑定限于真实 Core App 的名称与版本；静态业务内容由 App 的 GUI 声明提供。用户点击 espocket.card.open 时，框架暂停 Card，通过完整 App 的现有 Navigator 打开声明目标 Page。

Native Card 继续通过 CardModel 提供内容回调。两种呈现方式共享 App 身份、Home Space 横滑、Root/目标 Page、PWR Home 和系统生命周期语义；不承诺语言回调形式相同。

不建立另一套 Runtime，不直接分配共享 backend 的内部 App ID，不将系统 GUI 层或宿主模块能力交给 Runtime Card。后续可执行 JS Card、业务数据源和轻量业务动作须有明确的 Owner/权限/实例生命周期设计与上游支持，再独立扩展版本化 API。

## Consequences

- Runtime App 作者无需运行完整 App 即可提供可添加的专用 Card；复杂操作仍进入完整 App。
- 首版 Card 不调用 App JS，也不对停止 App 注册 Running Instance 或 AI capability。
- Card API 的可执行范围必须明确记录，不能把声明式呈现称为已支持 JS 业务回调。
- Package replacement 的稳定 Card 配置迁移仍需要实际更新事务 seam，本决定不解除该条件。

字段与作者职责见 [开发 API](../development/app-navigation-card-api.md)；上游事实见 [2026-10-02 核对](../upstream/status-2026-10-02.md)。
