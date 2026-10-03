# 04 — 采用官方 playback-only Audio path

**What to build:** 通过上游支持的 `PlaybackIface` 提供 Sound 与 Volume，同时保持 Codec Recorder 禁用。

**Blocked by:** 无。

**Status:** resolved

- [x] 已发布或明确采用的上游 path 能提供 playback 且不启用 recorder。
- [x] 采用官方修复后重新执行相关 clean build，记录锁定依赖和镜像 identity。
- [x] Settings Sound/Volume 真机验证真实播放及音量变化；Codec Recorder 保持关闭，记录物理观察和失败。
- [x] 按用户 2026-10-03 授权维护准确应用的 HAL patch；不手工改 managed_components，不创建私有 Audio framework。

实现与真实 open/spec 主机回归见 [2026-10-03 记录](../records/2026-10-03-playback-only-patch.md)。此前完全无声的失败和后续输出格式修正保留在听感记录中。

本次实际播放门槛使用 [2026-10-03 听感 probe 记录](../records/2026-10-03-audio-playback-probe.md)，不以仅调节 volume 成功代替播放。

## Resolution

2026-10-03：采用 ADR-0016 授权维护的 HAL playback-only 修复路径；原始 managed_components 不改，Recorder/AFE 保持关闭。实际 player 输出与 DAC 统一为 16000/stereo/16bit，81 项 host checks、完整构建、启动、官方 Playback/Storage 生命周期门槛通过。用户在修正 fixture `7a72035bd` 对实际出声、降低音量及 PWR Home 停止确认“都正常”，完成一次必要物理验收。

本票接受经过验证的 `audio-candidate` 路径；默认 production 的依赖清单与配置尚未合入 Audio，不能据此声称正式发布已完成。不含测试音的对应镜像及恢复结果见听感记录。重复 I2S disable 告警由 [07](07-fix-audio-playback-teardown.md) 独立承接，不把功能验收当作 teardown 告警已经消失。

2026-10-03 后续：用户授权默认组合合入；production 已采用上述配置与准确锁定的补充依赖，完整构建和启动通过。此处此前“尚未合入”为历史状态；当前结果见 [默认构建收尾](../records/2026-10-03-production-followup.md)，I2S teardown 的最终设备结果仍由 07 持有。
