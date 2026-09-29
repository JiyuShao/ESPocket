# 02 — 增加 Native 与 Runtime reclaim test seam

**What to build:** 默认关闭的 path，分别回收两种 App model 并使旧页面失效，同时不实现通用 low-memory killer。

**Blocked by:** 01 — 完成共享契约源码。

**Status:** ready-for-agent

- [ ] Native 与 Runtime 可以独立回收。
- [ ] 旧页面与 transient Overlay state 失效。
- [ ] Relaunch 从 App Root 开始。
