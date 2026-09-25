# ESPocket

**ESPocket is a lightweight application platform for ESP-powered smart devices, built on ESP-Brookesia.**

**ESPocket 是一个基于 ESP-Brookesia、面向 ESP 系列轻量智能设备的应用平台。**

ESPocket 负责产品平台层；ESP-Brookesia 提供基础应用框架。V0.x 只面向 Waveshare ESP32-S3-Touch-AMOLED-1.75C 开发和优化，但 ESPocket 不等同于 Circular Shell 或该硬件。

## 当前阶段

当前只实施 **M1 — ESPocket System**：

```text
app_main
   └── espocket::System
       └── CircularShell
           ├── Launcher
           ├── TestPage        # M1 临时，M2 删除
           └── ShellOverlay
               ├── StatusView
               ├── HomeIndicator
               └── HomeGesture
```

M1 只验证 System + Circular Shell，不验证通用 Native App 生命周期。M0 已由项目所有者于 2026-09-25 明确豁免，状态为 `WAIVED`，不是 `PASS`。

详细边界见 [`docs/PROJECT_DESIGN.md`](docs/PROJECT_DESIGN.md)，当前验收状态见 [`docs/milestones/M1_ACCEPTANCE.md`](docs/milestones/M1_ACCEPTANCE.md)。

## 构建

已验证基线为 ESP-IDF 6.0.1 与仓库中的 `firmware/dependencies.lock`。目标板选择器为 `esp32_s3_touch_amoled_1_75c`。

从仓库根目录执行：

```bash
export ESP_IDF_VERSION=6.0.1
export IDF_PATH="$HOME/.espressif/v6.0.1/esp-idf"
source "$IDF_PATH/export.sh"

idf.py -C firmware set-target esp32s3
idf.py -C firmware reconfigure

BOARD_PATH="$PWD/firmware/managed_components/espressif__brookesia_hal_boards/boards/waveshare/esp32_s3_touch_amoled_1_75c"
idf.py -C firmware gen-bmgr-config -b "$BOARD_PATH"
idf.py -C firmware build
```

`managed_components/`、`sdkconfig` 与 `components/gen_bmgr_codes/` 均为生成内容，不提交；`dependencies.lock` 必须保留。

## License

Apache License 2.0。见 [`LICENSE`](LICENSE)。
