# ESPocket Firmware

本目录包含 ESPocket 的 ESP-IDF firmware。构建以当前 checkout、`dependencies.lock` 和项目指定的 ESP-IDF 基线为输入。

## 前置环境

- ESP-IDF 6.0.1
- Target：`esp32s3`
- Board selector：`esp32_s3_touch_amoled_1_75c`
- Node.js：只在构建 Runtime App package 时需要

## 首次构建或重新生成配置

```bash
export IDF_PATH="$HOME/.espressif/v6.0.1/esp-idf"
source "$IDF_PATH/export.sh"

idf.py -C firmware set-target esp32s3
idf.py -C firmware reconfigure

BOARD_PATH="$PWD/firmware/managed_components/espressif__brookesia_hal_boards/boards/waveshare/esp32_s3_touch_amoled_1_75c"
idf.py -C firmware gen-bmgr-config -b "$BOARD_PATH"
idf.py -C firmware build
```

Board Manager 生成的 defaults 必须与同一 checkout 一起使用。切换依赖、Target 或 Board 配置后，应重新执行配置生成步骤。

## 增量构建

```bash
idf.py -C firmware build
```

## 文件职责

| Path | Role |
|---|---|
| `dependencies.lock` | 受版本控制的组件解析结果 |
| `sdkconfig` | 本机构建生成，不纳入版本控制 |
| `managed_components/` | 依赖解析生成，不纳入版本控制 |
| `components/gen_bmgr_codes/` | Board Manager 生成，不纳入版本控制 |
| `build/` | 构建输出，不纳入版本控制 |

阶段专属的构建、烧录和真机步骤由对应 Milestone acceptance 定义。
