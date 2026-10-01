# 08 — 连接主要 voice Provider

**What to build:** 已验证 XiaoZhi 或同等 Provider 接入同一 Assistant 与 authorization path，不成为第二个 Conversation Owner。

**Blocked by:** [05 本地 Assistant 语义](05-verify-cancellation-and-result-semantics.md)；已锁定 Provider dependency；[004/04 playback-only Audio](../../004-m4-device-capabilities/issues/04-adopt-playback-only-audio.md)。

**Status:** needs-info

- [ ] Provider dependency 与 API 存在于锁定 Platform Baseline。
- [ ] Voice input 映射到现有 User Intent 与 Action contract。
- [ ] Audio、cancellation 与 PWR 行为通过 hardware acceptance。
- [ ] 不引入第二套 capability registry、permission system 或 Conversation Owner。
