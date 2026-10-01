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

只约束一个组件的测试放在该组件的 `test/`；跨组件测试放在 `firmware/test/`。测试可以执行组件行为，也可以分析源码或资源，只要它对稳定约束做出可重复的断言。

无需硬件的统一检查入口：

```bash
python3 scripts/check.py
```

它只检查工作区，不自动格式化、修复或写入构建产物。C++ 行为测试在临时目录编译，需要支持 C++23 的 `clang++`；Settings 兼容检查需要先按锁定版本物化 managed components。默认不运行 Chrome；显式加 `--diagrams` 才运行架构图检查。完整 ESP-IDF build、烧录与真机验收独立执行。

例如，Shell 文档的结构测试运行方式为：

```bash
python3 -m unittest discover -s firmware/components/shell_circular/test -p 'test_*.py'
```

官方 Settings 导航适配绑定锁定版本。依赖升级前运行：

```bash
python3 -m unittest discover -s firmware/components/espocket_system/test -p 'test_*.py'
```

该测试检查锁定组件、页面资源与 Back 路由，并在主机执行 Adapter 委托和错误行为（需要支持 C++23 的 `clang++`）。固件 CMake 配置也会自动运行资源兼容检查，不匹配会阻止构建。升级时同次审查 manifest／lock、Adapter 映射和兼容测试，再按上文重新生成配置、完整构建并完成必要真机验收。生成的 `managed_components/` 改动不提交。

## GUI 资源

Circular Shell 与 Hello Native 各自以 `resources/gui.json` 为唯一 GUI 文档源码。CMake 在构建目录生成 `shell_gui.json`／`hello_gui.json` 副本，再用 `EMBED_TXTFILES` 嵌入；不同文件名避免 ESP-IDF 按 basename 生成的符号重名。生成副本不编辑、不提交，资源变化会触发重新配置与嵌入。

每个 Owner 的 `test/test_document_actions.py` 比较 GUI 事件声明、`on_start` 订阅与 `on_action` handler 集合，并保留事件唯一 Owner 检查。共享检查器只解析这些约定的结构，不解析整个 C++ 语言；改动 action 注册或处理形式时同步更新检查器和负例。

## 文件职责

| Path | Role |
|---|---|
| `dependencies.lock` | 受版本控制的组件解析结果 |
| `sdkconfig` | 本机构建生成，不纳入版本控制 |
| `managed_components/` | 依赖解析生成，不纳入版本控制 |
| `components/gen_bmgr_codes/` | Board Manager 生成，不纳入版本控制 |
| `build/` | 构建输出，不纳入版本控制 |

任务专属的构建、烧录和真机步骤由 [.scratch](../.scratch/README.md) 中的对应 ticket 定义，证据保存在同一 Effort 的 records。
