# 02 — 增加 Native 与 Runtime reclaim test seam

**What to build:** 默认关闭的 path，分别回收两种 App model 并使旧页面失效，同时不实现通用 low-memory killer。

**Blocked by:** [01 既有共享契约源码基线](01-complete-shared-contract-source.md)（已完成）；[014/01 Navigator](../../014-app-navigation-card-contract/issues/01-page-declaration-navigator.md) 与 [014/02 Back 分发](../../014-app-navigation-card-contract/issues/02-back-dispatch.md)。

**Status:** resolved

- [x] Native 与 Runtime 可以独立回收。
- [x] 旧页面与 transient Overlay state 失效。
- [x] Relaunch 从 App Root 开始。

## Resolution

2026-10-02：默认关闭的 Native/Runtime 独立回收入口完成，复用真实 Core stop 与 Navigator/Overlay 清理；生产边界五种配置主机测试、两种启用分支 ESP32-S3 交叉编译和普通固件完整构建通过。见 [源码与镜像证据](../records/2026-10-02-independent-reclaim-seam.md)。真机结果由 03 持有，不在本票虚报。
