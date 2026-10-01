# M7 Shell 亮度 OutputId 修复（2026-10-02）

## 问题与改动

原 Shell 的 Brightness Card 与 Quick Settings 亮度读写固定传 `OutputId = 0`；锁定版 Display Service 依据具体输出 ID 查找背光，而 `System::start_display()` 已从真实输出列表选出带触摸屏的 output。现在 System 构造 Circular Shell 时传入该 `display_output_id_`，Shell 的读、写及刷新均使用同一个 ID；没有有效 ID 时明确显示未知状态或返回错误。官方 Settings App 的亮度实现与服务接口未修改。

## 主机验证

- ESP-IDF 6.0.1 独立目录 `firmware/build/manual-clean-abs` 构建、链接和 App 分区大小检查通过；最小 App 分区剩余 43%。
- App 镜像 SHA-256：`a6ca7070078b66909a700ad017c58eb07caecc7cffd83c5283a5d42d3b7830a0`。
- `CONFIG_ESPOCKET_M6_RECLAIM_ON_TIMEOUT_TEST`、`CONFIG_ESPOCKET_M6_RESOURCE_TRACE` 与 M2 lifecycle stress 均关闭。
- 本轮没有刷写该 M7 镜像；设备仍运行 M6 已验收普通镜像。实际亮度变化、卡片与 Quick Settings 的可见反馈仍按 [M7 验收](../acceptance.md)取证。
