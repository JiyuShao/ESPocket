# 02 — 关闭 M7 source 与 build gate

**What to build:** Cards、Quick Settings、Edge Back 与直接 Launch Source 形成一套 clean、可构建且绑定真实 capability 的导航闭环。

**Blocked by:** 01 — 修复 brightness output identity。

**Status:** ready-for-agent

- [ ] Brightness 修复后重新执行现有 host/static gate。
- [ ] Card 与 Quick Settings capability error 以可预测方式失败。
- [ ] 不增加通用 Card SDK 或任意 history stack。
