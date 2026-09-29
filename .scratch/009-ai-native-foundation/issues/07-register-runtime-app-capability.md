# 07 — 注册一个 Runtime App capability

**What to build:** 可信 Runtime App 通过 Runtime/HostBridge admission 验证同一语义与 Running Instance lifetime。

**Blocked by:** 06 — 注册 Native capability；M5 package trust 与 Runtime isolation gate。

**Status:** needs-info

- [ ] Runtime manifest 与 HostBridge permission check 保持有效。
- [ ] Stop failure 不会泄漏 capability 或 keyboard ownership。
- [ ] Capability discovery 前，remote package identity 已受信任。
