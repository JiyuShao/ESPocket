# M6 Store 故障定向复测（2026-10-01）

## 对象

- 设备：Waveshare ESP32-S3-Touch-AMOLED-1.75C，USB 串口 `/dev/cu.usbmodem101`。
- 普通固件 App SHA-256：`786f618a56015fb714474e1b6b3a062611ee1f29313875e4a33715ed219cb9ab`；M6 回收测试开关关闭。
- 目的：复查 [2026-09-29 快速冒烟](2026-09-29-quick-device-smoke.md)中的 Store 任务栈溢出，不覆盖 M5 的在线 Store 稳定性门槛。

## 步骤与观察

用户从表盘上滑进入 Launcher，打开 Store，保持页面约 110 秒，不触发下载或安装，然后短按 PWR。用户确认 Store 持续显示、下方列表为空，PWR 后回到表盘。

串口记录 Store App 启动（uptime 325725 ms），网络状态为 `Offline`、`network_ready(false)`、`internet_ready(false)`；本地 Store cache index 缺失。期间两次记录 `Failed to show App Store message dialog: Message dialog is not supported by this system`。到 PWR 退出（uptime 435821 ms）之间，没有观察到任务栈溢出、panic、watchdog、assert 或重启；PWR 后串口记录 Store App 停止。串口停留区间约 110 秒。

## 判定与剩余范围

本次普通镜像的**离线 Store 定向停留与 PWR 退出通过**，没有复现旧镜像的 `SvcMgrSec1` 栈溢出。空列表与 `Offline` 状态一致；缺少可用的离线提示弹窗是独立的可见反馈缺口。

这次没有覆盖在线 Store 的 HTTP/TLS 路径；它属于独立的 M5 门槛，[M5 在线路径的既有崩溃证据](../../m5/records/2026-09-28-acceptance-report.md)仍有效，不应被这次离线稳定性观察抹掉。M6 的四条固定路径和单项检查没有 fatal signal，但本轮未跨重复操作采集资源趋势，因此该记录不能单独将 M6 的完整 failure scan 标为 PASS。
