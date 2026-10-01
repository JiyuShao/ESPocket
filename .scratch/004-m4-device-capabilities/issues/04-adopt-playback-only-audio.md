# 04 — 采用官方 playback-only Audio path

**What to build:** 通过上游支持的 `PlaybackIface` 提供 Sound 与 Volume，同时保持 Codec Recorder 禁用。

**Blocked by:** 官方 Brookesia HAL/Audio capability 变更。

**Status:** needs-info

- [ ] 已发布或明确采用的上游 path 能提供 playback 且不启用 recorder。
- [ ] 采用官方修复后重新执行相关 clean build，记录锁定依赖和镜像 identity。
- [ ] Settings Sound/Volume 真机验证真实播放及音量变化；Codec Recorder 保持关闭，记录物理观察和失败。
- [ ] 不引入 managed-component patch 或私有 Audio framework。
