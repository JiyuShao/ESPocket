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

## 测试

只约束一个组件的测试放在该组件的 `tests/`；跨组件测试放在 `firmware/tests/`。测试可以执行组件行为，也可以分析源码或资源，只要它对稳定约束做出可重复的断言。

这是当前目录约定；[固件结构重构计划](../.scratch/013-firmware-structure-refactor/spec.md)将统一迁至 ESP-IDF 的 `test/` 目录。迁移完成前，现有命令继续使用 `tests/`。

例如，Shell 文档的结构测试运行方式为：

```bash
python3 -m unittest discover -s firmware/components/shell_circular/tests -p 'test_*.py'
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
