# 02 — 增加可控 reclaim fallback seam

**What to build:** 默认关闭的 test path，使当前 resume target 失效，让 hardware acceptance 能证明回退到 Watch Face。

**Blocked by:** 01 — 实现 Watch Face Home 与 Display State。

**Status:** ready-for-agent

- [ ] Test seam 不会在普通产品使用中激活。
- [ ] 使 target 失效时不引入通用 memory manager。
- [ ] 下一次 wake 到达 Watch Face，不重启 App。
