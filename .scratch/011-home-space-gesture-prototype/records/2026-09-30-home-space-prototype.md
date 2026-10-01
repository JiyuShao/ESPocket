# Home Space 真机交互样机记录（阶段外）

- 日期：2026-09-30
- 类型：可回退样机；不构成 M7 acceptance，也不改变 M7 `NOT ENTERED`
- 设备：ESP32-S3-Touch-AMOLED-1.75C，经 `/dev/cu.usbmodem1101` 刷入 App 分区 `0x60000`
- 镜像：`firmware/build/manual-clean-abs/espocket.bin`
- SHA-256：`539e29ba11c3ad627c381884110feca62307ea54aa63dfdcd8b8323aa9e75c82`
- 大小：`0x5d3560`；分区空余 `0x46daa0`（43%）

## 已验证

- 现有生成构建图完成编译、链接与分区大小检查。
- `esptool` 完成 App 分区写入并报告 `Hash of data verified`。
- Shell JSON 可解析；Shell 单测 1 项通过；`python3 scripts/docs/check.py` 通过。

## 待真机观察

- Launcher 纵向列表的实际滚动范围、顶部下拉拉伸与阈值提示。
- 越过阈值松手返回表盘，且该触摸不误开 App。
- Quick Settings 上滑返回、Shell 常驻状态栏移除、PWR 与息屏恢复。

标准 `idf.py build` 当前受锁定版 Brookesia HAL 的缺失 Kconfig option 阻断。本次镜像使用此前生成的构建图增量链接；它不是干净构建门槛的替代证据。

样机任务见[本地 spec](../spec.md)。
