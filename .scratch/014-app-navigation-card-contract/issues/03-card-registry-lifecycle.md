# 03 — App Card 注册与生命周期

**What to build:** ESPocket 管理 App Card 的注册、Home Space 配置、可见生命周期和目标 Page 打开；App 提供内容、轻量操作及数据来源。

**Blocked by:** [01 Page Navigator](01-page-declaration-navigator.md)；[02 Back 分发](02-back-dispatch.md)。

**Status:** ready-for-agent

- [ ] 同一 `appId + cardId` 最多配置一次，不同 Card ID 可并存，用户可添加、移除和排序左右 Card。
- [ ] Home Space 拥有横滑，Card 拥有纵向交互和轻量操作；多级流程进入完整 App。
- [ ] Card 离屏可暂停或销毁，重新可见请求新数据；打开完整 App 时 Card 暂停。
- [ ] 卸载或更新移除 Card ID 时删除对应配置并记录原因；Quick Settings 与 Launcher 保持固定。

## Comments

- 2026-10-02（夜间）：先完成真实 C++ CardRegistry 的声明身份、左右增删/排序、原子配置替换、更新/卸载删除与原因通知。与 PageNavigator 复用同一个声明校验，不建立第二份页面栈。组件尚未接 Core 安装/卸载、Shell Card 呈现、UI 可见生命周期和 NVS 配置；整体 acceptance 保持未勾选。详见 [Registry 组件证据](../records/2026-10-02-card-registry.md)。
