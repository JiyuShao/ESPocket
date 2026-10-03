# 07 — 修复 playback 退出时重复关闭 I2S

**What to build:** 在实际 Codec/Board Manager Owner 边界消除 playback 退出时重复 disable 已关闭 TX 的错误日志，保留正确资源释放与再次打开行为。

**Blocked by:** 无；先读取锁定 codec 与 Board Manager 释放顺序，确定关闭职责。

**Status:** ready-for-agent

- [ ] 复现 Home 退出时 `i2s_channel_disable: the channel has not been enabled yet`，定位真实调用顺序。
- [ ] 在实际 Owner 内补充失败回归与最小修复；如需上游补丁，遵循 ADR-0016 的身份/hash/准确应用要求。
- [ ] 相关主机检查、完整构建及自动播放 → Home → 再次播放检查通过，退出不再报重复 disable。

来源见 [2026-10-03 听感记录](../records/2026-10-03-audio-playback-probe.md)。004/04 的真实出声、音量与停止已验收；本票不要求重复人工听音，除非修复引入具体物理风险。
