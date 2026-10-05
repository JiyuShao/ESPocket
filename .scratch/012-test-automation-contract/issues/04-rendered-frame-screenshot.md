# 04 — 最终渲染画面截图

**What to build:** 通过受开发者模式控制的 USB Test Adapter 捕获最终 RGB565 渲染帧并导出 PNG，直接识别 Store 系统提示。

**Blocked by:** none

**Status:** resolved

- [x] 使用 LVGL 公开刷新事件，不替换 HAL flush，不修改上游。
- [x] 验证完整覆盖、字节顺序、分块边界、准入和缓存释放；主机检查整帧摘要。
- [x] 仓库检查和完整 firmware 构建通过。
- [x] app-only 刷入准确镜像，hello identity/capabilities 和启动通过。
- [x] 导出实际设备 PNG，保存独立 attempt 与摘要，识别 Store 提示。

## Comments

2026-10-04：用户已授权截图实现、构建、app-only 刷写和设备捕获。保留既有 LittleFS 与 NVS；证据为 rendered-frame，不替代物理面板验收。

证据见[截图记录](../records/2026-10-04-rendered-frame-screenshot.md)。

## Resolution

2026-10-04：最终镜像 f3fdd7e82 完成启动与默认 512-byte 分块实际 PNG 导出，包含 Local 加载提示和最终列表，整帧摘要及 release 通过。栈溢出、发送缓冲不足及中途缓存失效 attempt 均保留；失败不生成 PNG。设备画面已能直接查看，Flappy Bird 当前显示 Installed；005 的安装确认、receipt 和启动验收不由本票替代。
