# 两轮导航与服务变化记录

- 日期：2026-10-02
- 设备：ESP32-S3-Touch-AMOLED-1.75C
- 样机 App 镜像 SHA-256：`8c5a877bf65291c0c8b6f8a245a952fc769684fbfd194bb0a42c843500dd5bbb`
- 原始串口：本地临时文件 `/private/tmp/espocket-m7-five-loops.log`，不进入仓库

## 门槛变更

用户在操作几轮且均正常后明确要求停止继续做五轮，并降低重复验收次数。M7 的完整导航、Wi-Fi 真实切换和亮度真实变化固定门槛均改为两次；单次路径覆盖保留。此变更在记录时作出，不能把未观察到的步骤补记为成功。

## 真机结果

| Attempt | 串口时间与可核对顺序 | 用户观察 |
|---|---|---|
| 1 | 13–41 s：Watch Face → Battery Card → Watch Face → Brightness Card（背光变化）→ Watch Face → Quick Settings（Wi-Fi 从连接态停止）→ Watch Face → Launcher → Native Root → Detail → Root → PWR Watch Face | 用户报告操作正常 |
| 2 | 47–74 s：同样的 Battery/Brightness 往返、Quick Settings 上滑返回、Launcher → Native Root → Detail → Root → PWR Watch Face；其中 Detail/Root 又重复一次 | 用户报告操作正常 |

独立服务证据：串口记录多次实际背光设置，至少两次发生在 Brightness Card 或 Quick Settings 操作期间；用户确认屏幕亮度与文字同步变化、页面保持。Wi-Fi 在约 22 s 与 101 s 两次从运行态切到初始化态，之后又出现连接恢复；用户确认 Quick Settings 文案变化并留在该页。第二轮完整导航期间未捕获独立的 Wi-Fi 状态变化，因此 Wi-Fi 的两次真实切换按整个采集窗口计数，不将其归入第二轮。

采集窗口未检出 panic、watchdog、assert；这只覆盖该样机镜像和采集时段。随后源码补充 Navigator 跨任务组同步，并调整 Back 回调，使 PWR Home 清栈无需等待 App 回调；并发主机测试通过。该后续镜像 SHA-256 为 `6d5837796dc7ab5dc952b6e7d952d525368b278d711a88b6a4d4e658474077c3`，已仅写入 App 分区且通过写入哈希校验；串口自动检查记录 `ESPocket started`、无 panic。用户要求不再重复真机循环，因此本次触控结果属于先前样机镜像，不能算作后续镜像的完整物理验收。
