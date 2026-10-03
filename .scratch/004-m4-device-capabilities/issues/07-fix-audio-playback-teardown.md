# 07 — 修复 playback 退出时重复关闭 I2S

**What to build:** 在实际 Codec/Board Manager Owner 边界消除 playback 退出时重复 disable 已关闭 TX 的错误日志，保留正确资源释放与再次打开行为。

**Blocked by:** None.

**Status:** resolved

- [x] 复现 Home 退出时 `i2s_channel_disable: the channel has not been enabled yet`，定位真实调用顺序。
- [x] 在实际 Owner 内补充失败回归与最小修复；如需上游补丁，遵循 ADR-0016 的身份/hash/准确应用要求。
- [x] 相关主机检查、完整构建及自动播放 → Home → 再次播放检查通过，退出不再报重复 disable。

来源见 [2026-10-03 听感记录](../records/2026-10-03-audio-playback-probe.md)。004/04 的真实出声、音量与停止已验收；本票不要求重复人工听音，除非修复引入具体物理风险。

本轮最小失败、真实释放顺序与候选补丁见 [I2S 清理记录](../records/2026-10-03-i2s-teardown.md)；完整设备门槛完成后更新状态。

## Resolution

2026-10-04：实际 Board Manager 0.5.15 修复按驱动实时状态释放 I2S。原源码失败回归、TX/RX 与 peer 状态及失败保留测试、默认完整构建通过；独立 fixture 474d7dc30 的两轮真实 Play → Home → replay PASS，均收到 Owner Playing、停止并删除自有 WAV，没有重复 disable。设备旧 V2 文件保留；UUID fixture 前置阻塞与 USB 短暂断连失败有记录，未冒充验收。恢复普通 production 镜像，不重复已有的物理听感验收。
