# M6 reclaim 测试镜像记录（2026-10-01）

## 镜像与刷写

- 固定 Git 基点：`5e35f0a92cc21a9a0515bde69b779670cf38b21e`；镜像包含未提交的工作区改动，不能仅凭该 commit 重建。
- 设备：ESP32-S3，USB 串口 `/dev/cu.usbmodem101`；烧录工具识别 revision v0.2、8 MB PSRAM。
- 隔离构建目录：`firmware/build/m6-reclaim`；`CONFIG_ESPOCKET_M6_RECLAIM_ON_TIMEOUT_TEST=y`。
- App 镜像 SHA-256：`e5584cdf0462d4481fb9d465b86315110da7e8b973cb2b6ade77ad082d492948`。
- ESP-IDF 6.0.1 编译、链接和分区大小检查通过。App 镜像 0x5d3670 bytes；最小 App 分区剩余 43%。
- 经 `/dev/cu.usbmodem101` 写入 bootloader、partition table、LittleFS 和 App；esptool 对各段报告 `Hash of data verified`，并完成硬复位。

## 真机结果

开始固定循环前，串口曾记录一次 `M6 display state: Off`，但没有 `M6_RECLAIM_TEST` 事件；它不计入回收路径。随后在同一测试镜像和串口会话中，用户按顺序执行 5 次「Native Detail → 自动息屏 → PWR Wake」，并确认五次亮屏都是表盘，无黑屏、重启或其他异常。

| Attempt | 自动息屏 uptime (ms) | App 停止与回收标记 | PWR Wake uptime (ms) | 物理屏幕 |
|---|---:|---|---:|---|
| 1 | 15864905 | `App stopped: id(1)`；`M6_RECLAIM_TEST` | 15873462 | 表盘，正常 |
| 2 | 15909409 | `App stopped: id(1)`；`M6_RECLAIM_TEST` | 15910511 | 表盘，正常 |
| 3 | 15946220 | `App stopped: id(1)`；`M6_RECLAIM_TEST` | 15951120 | 表盘，正常 |
| 4 | 15985991 | `App stopped: id(1)`；`M6_RECLAIM_TEST` | 15988419 | 表盘，正常 |
| 5 | 16021636 | `App stopped: id(1)`；`M6_RECLAIM_TEST` | 16024101 | 表盘，正常 |

每轮串口都在 Wake 前记录 App 停止和 `M6_RECLAIM_TEST stopped resume target app_id=1`，随后记录 `M6 display state: On`、`M6 Home: Watch Face`、`M6 display state: Wake`。各轮停止与 Wake 之间没有 App 启动事件；下一次 App 启动发生在该轮 Wake 之后。采集窗口未见 panic、watchdog 或重启。五次固定回收回退路径通过；后续还出现额外成功循环，不用于替代固定五次。

M6 其他硬件门槛仍未全部完成，整体保持 `IN PROGRESS`。

此镜像只用于回收回退路径。普通 App 自动息屏后恢复必须用关闭测试开关的候选镜像另行验证。

## 恢复普通固件

固定循环完成后，使用同一工作区另建 `firmware/build/m6-normal`，确认 `CONFIG_ESPOCKET_M6_RECLAIM_ON_TIMEOUT_TEST` 未设置。ESP-IDF 6.0.1 编译、链接及分区大小检查通过；普通 App 镜像 SHA-256 为 `786f618a56015fb714474e1b6b3a062611ee1f29313875e4a33715ed219cb9ab`。仅将该 App 镜像写入 `0x60000`，esptool 报告 `Hash of data verified` 并硬复位，其他分区未在这次恢复刷写中改动。

刷回普通镜像后，用户确认一次 Native Detail 自动息屏、PWR 唤醒仍显示 Native Detail。这是屏幕冒烟结果；该次没有同步采集到 Wake 串口日志，因此不计入普通恢复路径的正式 5 次循环，也不与回收测试结果混算。

后续普通镜像串口会话记录了多轮完整的 `M6 display state: Off` → `On` → `Wake`。用户按要求执行固定五次循环，确认每次唤醒都回到 Native Detail。按采集顺序选取的五组完整串口转移如下；监听续接时有一次 Off 未被采到，该不完整转移没有替代固定循环中的完整证据。

| Attempt | Off uptime (ms) | Wake uptime (ms) | 物理屏幕 |
|---|---:|---:|---|
| 1 | 3524732 | 3526173 | Native Detail |
| 2 | 3556194 | 3557800 | Native Detail |
| 3 | 3587820 | 3593746 | Native Detail |
| 4 | 3666468 | 3667922 | Native Detail |
| 5 | 3697964 | 3699729 | Native Detail |

固定窗口未出现 `M6_RECLAIM_TEST`、App 停止、panic 或重启。正常固件的同页恢复路径 5/5 通过；此结论只覆盖上述路径，不代表 M6 整体 PASS。
