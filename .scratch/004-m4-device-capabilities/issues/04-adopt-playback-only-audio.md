# 04 — 采用官方 playback-only Audio path

**What to build:** 通过上游支持的 `PlaybackIface` 提供 Sound 与 Volume，同时保持 Codec Recorder 禁用。

**Blocked by:** playback-only candidate 的实际板级 Playback/Sound/Volume 验收；启动缓冲问题已有配置修复与启动通过证据。

**Status:** ready-for-agent

- [ ] 已发布或明确采用的上游 path 能提供 playback 且不启用 recorder。
- [ ] 采用官方修复后重新执行相关 clean build，记录锁定依赖和镜像 identity。
- [ ] Settings Sound/Volume 真机验证真实播放及音量变化；Codec Recorder 保持关闭，记录物理观察和失败。
- [ ] 按用户 2026-10-03 授权维护准确应用的 HAL patch；不手工改 managed_components，不创建私有 Audio framework。

候选实现与真实 open/spec 主机回归见 [2026-10-03 记录](../records/2026-10-03-playback-only-patch.md)。Recorder 保持关闭，完整 optional-backend 构建通过；40 行候选启动通过，听感验收失败：Mute 关闭且真实 Playing/PCM 写入成功，用户仍报告完全无声，继续排查 codec/PA/板级路径。

本次实际播放门槛使用 [2026-10-03 听感 probe 记录](../records/2026-10-03-audio-playback-probe.md)，不以仅调节 volume 成功代替播放。
