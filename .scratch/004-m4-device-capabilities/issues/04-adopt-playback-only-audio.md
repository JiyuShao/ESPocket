# 04 — 采用官方 playback-only Audio path

**What to build:** 通过上游支持的 `PlaybackIface` 提供 Sound 与 Volume，同时保持 Codec Recorder 禁用。

**Blocked by:** 官方 Brookesia HAL/Audio capability 变更。

**Status:** needs-info

- [ ] 已发布或明确采用的上游 path 能提供 playback 且不启用 recorder。
- [ ] Clean build 与 Settings Sound/Volume 真机 acceptance 通过。
- [ ] 不引入 managed-component patch 或私有 Audio framework。
