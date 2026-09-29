# 构建 ESPocket firmware

> 文档类型：操作指南。版本 identity 以 `firmware/dependencies.lock` 和当前 Milestone 证据为准。

## 前置环境

- ESP-IDF 6.0.1
- 目标 `esp32s3`
- Board selector `esp32_s3_touch_amoled_1_75c`
- Node.js 仅在构建 Runtime App 或生成架构图时需要

## 首次或 clean build

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

Board Manager 生成的 defaults 必须与当前 checkout 一起使用。`managed_components/`、`sdkconfig`、`firmware/build/` 和 `firmware/components/gen_bmgr_codes/` 是生成内容；`firmware/dependencies.lock` 是受控输入。

## 文档与架构图

```bash
node docs/design/architecture/tools/generate-diagrams.mjs
python3 scripts/check-docs.py
```

第二条命令检查相对链接、锚点、Context 格式、`.scratch` 状态、生成图一致性和 SVG 布局。

## 结果归档

Milestone 构建或真机门槛产生的原始记录写入新的 `docs/milestones/evidence/<stage>/` 文件，并从对应 `acceptance.md` 链接。已经被验收引用的证据文件保持不可变。
