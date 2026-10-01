# 03 — App Card 注册与生命周期

**What to build:** ESPocket 管理 App Card 的注册、Home Space 配置、可见生命周期和目标 Page 打开；App 提供内容、轻量操作及数据来源。

**Blocked by:** 01、02；App Card 机制不并入 M7 真机手势样机。

**Status:** ready-for-agent

- [ ] 同一 `appId + cardId` 最多配置一次，不同 Card ID 可并存，用户可添加、移除和排序左右 Card。
- [ ] Home Space 拥有横滑，Card 拥有纵向交互和轻量操作；多级流程进入完整 App。
- [ ] Card 离屏可暂停或销毁，重新可见请求新数据；打开完整 App 时 Card 暂停。
- [ ] 卸载或更新移除 Card ID 时删除对应配置并记录原因；Quick Settings 与 Launcher 保持固定。
