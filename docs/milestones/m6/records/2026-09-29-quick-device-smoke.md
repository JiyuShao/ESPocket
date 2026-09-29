# M6 真机快速冒烟记录（2026-09-29）

## 对象和固件

- 设备：Waveshare ESP32-S3-Touch-AMOLED-1.75C；串口 `/dev/cu.usbmodem1101`。实测 ESP32-S3、8 MB PSRAM、32 MB Flash。
- 刷写范围：仅 App 分区 `0x60000`；未擦写 NVS 或 LittleFS。刷写前 App 镜像已备份，SHA-256 为 `d1050910417bea4fa9f455d6041ad4a4e3d13b12b539f3844821c4f56fa46cfb`。
- 本轮最终实机 App SHA-256：`8e236378bcf606a3796df4ac9680a5cd3489b6b86ed1845c5061377c58252ef6`。esptool 报告 `Hash of data verified`。
- 影响判定的脱敏串口事实已归纳在下表；原始日志不纳入源码树。

## 观察

| 项目 | 结果 |
|---|---|
| 启动 | 修复版连续两次启动均记录 `Circular Shell started`、`PWR monitor ready on GPIO3`、`ESPocket started`。刷写前旧镜像首次显示 Launcher；不能把旧镜像的结果算入本轮。 |
| PWR 短按 | 用户在实机观察到一次完整的「Native → 表盘 → 息屏 → 亮屏」顺序。串口对应记录 Native 停止、页面转为 `watch_face`、`M6 display state: Off`、`On`、`Wake`。固定 5 次验收中只完成 1 次观察。 |
| 自动息屏后恢复 | 待实机确认同一 Native Detail 页及导航位置；本轮串口摘录尚不能证明。 |
| 异常 | 同一串口会话曾进入 App Store 路径，随后 `SvcMgrSec1` 任务栈溢出并重启。M5 Store 已有阻塞项；本次故障仍需保留，不能将 failure scan 标为 PASS。 |

## 本轮修复与判定

最初刷入的离线候选因 Shell 文档重复使用 `shell.step_brightness` 和 `shell.open_settings` 动作而无法启动；改为各按钮独立 action 后，Shell 可启动。随后发现旧 PWR 监听走 TCA9554 EXIO4，和 1.75C 原理图不符；改为读取 `SYS_OUT` 所接的 GPIO3 后，PWR 路径在真机可用。唯一动作 ID 的回归测试及固件构建通过。

这只是快速冒烟：M6 保持 `IN PROGRESS`。冷启动、自动息屏恢复、回收目标降级及单项检查仍须按 [M6 验收规范](../acceptance.md)完成；Store 栈溢出须另行处理。
