# 03 — 增加本地 Assistant 入口

**What to build:** 由系统控制的 single-turn 本地入口，可将已确认用户目标映射到 brightness semantic Action，不选择 network 或 voice Provider。

**Blocked by:** 02 — 构建 brightness semantic Adapter。

**Status:** ready-for-agent

- [ ] 直接 brightness goal 可以执行并报告结果。
- [ ] “我看不清”等模糊目标在任何 Action 前请求澄清。
- [ ] 入口持续响应 PWR，且不依赖 model/network。
- [ ] UI 是最小真实产品入口，不预建通用 Overlay framework。
