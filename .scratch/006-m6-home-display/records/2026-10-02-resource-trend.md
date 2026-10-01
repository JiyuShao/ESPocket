# M6 资源趋势真机复测（2026-10-02）

## 镜像与采样点

- 设备：Waveshare ESP32-S3-Touch-AMOLED-1.75C，USB 串口 `/dev/cu.usbmodem101`。
- 资源诊断 App 镜像 SHA-256：`7eaa530ad5ae18284e3a77fbed6804282852ea50029316cf31eb599cedead0bb`。
- 独立构建目录 `firmware/build/m6-resource`；`CONFIG_ESPOCKET_M6_RESOURCE_TRACE=y`，M2 lifecycle stress 与 M6 reclaim 测试开关均关闭。ESP-IDF 6.0.1 构建、链接和分区大小检查通过；最小 App 分区剩余 43%。
- 仅写入 App 分区 `0x60000`，esptool 报告 `Hash of data verified`；NVS 与 LittleFS 未擦写。
- 诊断开关在表盘亮屏、短按 PWR 即将息屏时读取 internal/PSRAM 的 free 与 largest block。这个采样点位于 Native App 已停止、表盘可见之后，便于比较同一状态。开关默认关闭，不进入普通镜像。

## 真机循环与串口

用户按要求完成 10 轮「表盘 → Launcher → Native Detail → PWR Home → 表盘 → PWR Off → PWR Wake → 表盘」，确认每轮显示顺序正确，无黑屏或重启。连续串口窗口记录 12 次 Native 启动、12 次停止、13 次 `Off` 与 13 次 `Wake`；窗口还包含正式 10 轮前后的额外操作，不能将这些事件数当作固定 10 轮的逐次编号。窗口未见 panic、watchdog、assert 或 fatal signal。

资源采样序号证明固件执行到第 10 个同状态检查点。USB 串口只完整采到其中 5 行；缺失序号不填造数值，也不把额外操作计为补测：

| Sample | Internal free (B) | PSRAM free (B) | Internal largest (B) | PSRAM largest (B) |
|---:|---:|---:|---:|---:|
| 2 | 53,835 | 2,456,144 | 40,960 | 2,228,224 |
| 4 | 53,835 | 2,456,192 | 40,960 | 2,228,224 |
| 7 | 53,835 | 2,456,192 | 40,960 | 2,228,224 |
| 8 | 53,835 | 2,456,152 | 40,960 | 2,228,224 |
| 10 | 53,835 | 2,456,172 | 40,960 | 2,228,224 |

首末完整样本的四项变化分别为 `0 / +28 / 0 / 0 B`。覆盖早期、中期与第 10 次检查点的可用数据均未呈持续下降；该结论限于这次 Native Detail → Home/Off/Wake 诊断窗口，不声称所有系统负载都无泄漏。

## 恢复普通镜像

诊断结束后，仅将普通 App 镜像 `firmware/build/m6-normal/espocket.bin` 写回 `0x60000`；SHA-256 为 `786f618a56015fb714474e1b6b3a062611ee1f29313875e4a33715ed219cb9ab`，与先前四条固定路径的验收镜像一致。esptool 再次报告 `Hash of data verified` 并硬复位。NVS 与 LittleFS 未擦写。用户确认恢复后设备正常显示表盘。
