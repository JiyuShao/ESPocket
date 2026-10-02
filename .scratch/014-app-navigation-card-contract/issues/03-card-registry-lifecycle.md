# 03 — App Card 注册与生命周期

**What to build:** ESPocket 管理 App Card 的注册、Home Space 配置、可见生命周期和目标 Page 打开；App 提供内容、轻量操作及数据来源。

**Blocked by:** [01 Page Navigator](01-page-declaration-navigator.md)；[02 Back 分发](02-back-dispatch.md)。

**Status:** ready-for-agent

- [x] 同一 `appId + cardId` 最多配置一次，不同 Card ID 可并存，用户可添加、移除和排序左右 Card。
- [x] Home Space 拥有横滑，Card 拥有纵向交互和轻量操作；多级流程进入完整 App。
- [x] Card 离屏可暂停或销毁，重新可见请求新数据；打开完整 App 时 Card 暂停。
- [ ] 卸载或更新移除 Card ID 时删除对应配置并记录原因；Quick Settings 与 Launcher 保持固定。

## Comments

- 2026-10-02（夜间）：先完成真实 C++ CardRegistry 的声明身份、左右增删/排序、原子配置替换、更新/卸载删除与原因通知。与 PageNavigator 复用同一个声明校验，不建立第二份页面栈。组件尚未接 Core 安装/卸载、Shell Card 呈现、UI 可见生命周期和 NVS 配置；整体 acceptance 保持未勾选。详见 [Registry 组件证据](../records/2026-10-02-card-registry.md)。
- 2026-10-02（夜间续）：完成同步 CardSession 生命周期组件：首次创建、重新可见刷新、离屏暂停、切换/释放销毁、打开完整 App 前暂停、失败和重入防护。Registry 移除通过 Owner 转发 invalidate；实际 Shell/Core/提供者/NVS 仍未连接，保持整票开放。见 [生命周期组件证据](../records/2026-10-02-card-session.md)。

- 2026-10-02（用户恢复后）：Core/NVS/Shell/Native 提供者、Owner 动作队列与文档释放已接通，前三项源码条件完成。普通卸载和 Native 更新已实现，Runtime package replacement 的配置保留及更新原因尚缺真实事务 seam，最后一项保持未勾选；整票保持开放。见 [Owner 与呈现证据](../records/2026-10-02-card-owner-presentation.md)。
