# 08 — 单列 Agent Manager 与 XiaoZhi 接入

**What to build:** 独立设计并验证 Brookesia Agent Manager 与 XiaoZhi Provider 接入同一 Assistant 和 authorization path，保持现有 Conversation、Owner 与授权边界。

**Blocked by:** [05 本地 Assistant 语义](05-verify-cancellation-and-result-semantics.md)；已锁定 Provider dependency；[004/04 playback-only Audio](../../004-m4-device-capabilities/issues/04-adopt-playback-only-audio.md)。

**Status:** needs-info

- [ ] Provider dependency 与 API 存在于锁定 Platform Baseline。
- [ ] Voice input 映射到现有 User Intent 与 Action contract。
- [ ] Audio、cancellation 与 PWR 行为通过 hardware acceptance。
- [ ] 不引入第二套 capability registry、permission system 或 Conversation Owner。

## Comments

2026-10-04：用户要求 Agent Manager / XiaoZhi 单列。继续由本票持有依赖、会话/音频/MCP 映射及准入设计；不混入 019 的 Files、手机配网和开发诊断计划。本轮只登记归属，不选择模型或新增实施授权，独立完整设计仍待本票收敛。
