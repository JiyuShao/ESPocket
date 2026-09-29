# 06 — 注册一个 Native App capability

**What to build:** 一个真实 Native App capability，只在其 Running Instance 存在期间注册，并使用已验证的 authorization/result contract。

**Blocked by:** 05 — 验证 cancellation 与 result 语义。

**Status:** ready-for-agent

- [ ] Stop、crash 与 restart 使旧 handle 和 subscription 失效。
- [ ] Relaunch 创建新 capability identity。
- [ ] Persistent behavior 移到 Service，不延长 App lifetime。
