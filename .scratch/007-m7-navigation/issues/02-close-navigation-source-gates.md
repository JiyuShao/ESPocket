# 02 — 关闭 M7 source 与 build gate

**What to build:** Cards、Quick Settings、App 子页面默认可见 Back 与 Edge Back、Root 无 Back 和 PWR Home 形成一套可构建且绑定真实 capability 的导航闭环。

**Blocked by:** 01 — 修复 brightness output identity；[014/01 Page Navigator](../../014-app-navigation-card-contract/issues/01-page-declaration-navigator.md) 与 [014/02 Back dispatch](../../014-app-navigation-card-contract/issues/02-back-dispatch.md) 的 Native 路径。

**Status:** ready-for-agent

- [ ] Brightness 修复后重新执行现有 host/static gate。
- [ ] Card 与 Quick Settings capability error 以可预测方式失败。
- [ ] ESPocket 为完整 App 子页面提供默认可见 Back 与 Edge Back；Root 无 Back。App 自带 Back 时不重复显示，App 可同时关闭默认入口，多级 App 自带可见 Back。
- [ ] Home Space 反向滑动和 Launcher 顶部下拉不触发 App 的 Edge Back。
- [ ] 不增加通用 Card SDK 或任意 history stack。

## Comments

- 2026-10-01：原任务为「Cards、Quick Settings、Edge Back 与直接 Launch Source 形成一套 clean、可构建且绑定真实 capability 的导航闭环」。[ADR-0011](../../../docs/adr/0011-app-root-has-no-back.md) 将 App Root Back 改为 PWR Home，当前任务范围按上文执行；保留原描述作为决策历史。
- 2026-10-02：原依赖只列 Brightness ticket，但此 ticket 的默认 Back、Root 无 Back 和页面栈需要先由 014/01–02 提供 Native 实现；014 原先反向等待 M7 source gate，已消除该循环。Runtime 绑定及 App Card 不计入本 M7 source gate。
