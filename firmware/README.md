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

只约束一个组件或 Native App 的测试放在该 Owner 的 `test/`；跨组件测试放在 `firmware/test/`。测试可以执行组件行为，也可以分析源码或资源，只要它对稳定约束做出可重复的断言。

无需硬件的统一检查入口：

```bash
python3 scripts/check.py
```

它只检查工作区，不自动格式化、修复或写入构建产物。C++ 行为测试在临时目录编译，需要支持 C++23 的 host 编译器（默认 `clang++`，可用 `CXX` 指定）；Settings 兼容检查和 Runtime JSON 边界测试需要先按锁定版本物化 managed components；真实 Runtime 样例动作测试使用 Node.js 22。默认不运行 Chrome；显式加 `--diagrams` 才运行架构图检查。完整 ESP-IDF build、烧录与真机验收独立执行。

例如，Shell 文档的结构测试运行方式为：

```bash
python3 -m unittest discover -s firmware/components/shell_circular/test -p 'test_*.py'
```

官方 Settings 导航适配绑定锁定版本。依赖升级前运行：

```bash
python3 -m unittest discover -s firmware/components/espocket_system/test -p 'test_*.py'
```

该测试检查锁定组件、页面资源与 Back 路由，并在主机执行 Adapter 委托和错误行为（需要支持 C++23 的 host 编译器（默认 `clang++`，可用 `CXX` 指定））。固件 CMake 配置也会自动运行资源兼容检查，不匹配会阻止构建。升级时同次审查 manifest／lock、Adapter 映射和兼容测试，再按上文重新生成配置、完整构建并完成必要真机验收。生成的 `managed_components/` 改动不提交。

## USB 合成输入回归

启用设备开发者模式并刷入具有 touch/PWR/snapshot/release capability 的固件后，使用 [interaction_driver.py](../scripts/firmware/interaction_driver.py) 执行单次自动路径。它不自动刷写、重启或开启模式；需要 `pyserial`，可使用 ESP-IDF Python 环境。必须显式指定设备清单 ID 和期望镜像 identity。CLI、466px profile 与报告格式见 [交互测试协议](../docs/development/interaction-test-protocol.md)。输出仅证明 `synthetic-input`，不能满足 GPIO、触摸硬件或视觉条件。

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

## 源码与生成目录

- `components/` 保存 ESPocket System、Circular Shell、导航和测试 Adapter 等系统 component。
- `native_apps/<app>/` 保存自有 Native App，顶层 CMake 通过 `EXTRA_COMPONENT_DIRS` 发现；每个 App 自有 CMakeLists，System 显式安装。
- `runtime_apps/<app>/` 保存 Runtime App 源码及工具配置；两种 Reference App 为 `native_apps/hello/` 与 `runtime_apps/hello/`，manifest ID 不随目录变化。
- LittleFS 镜像输入位于当前 build tree 的 `littlefs-root/`（默认 `firmware/build/littlefs-root/`）。System 的 `project_include.cmake` 通过 Brookesia 公开路径配置接口在资源 staging 前指定该路径；设备挂载仍为 `/littlefs`，App 根仍为 `/littlefs/apps`。
- `managed_components/`、`components/gen_bmgr_codes/`、本地 `sdkconfig` 与 `sdkconfig.old` 保持工具约定位置并忽略。Runtime App 的 `build/`、`dist/`、`node_modules/` 也忽略；禁止提交这些生成物或重新建立旧的 `firmware/littlefs/` 输入目录。
- Component 的公开头文件依赖列入 `REQUIRES`，实现依赖列入 `PRIV_REQUIRES`。System 配置位于自有 `Kconfig`，固件版本由顶层 `PROJECT_VER` 注入 SystemInfo；App manifest 版本仍由 App 自有。
- `compat/` 是显式、可移除的兼容 seam；每个文件记录影响版本、上游问题和删除条件。当前 attributes 告警豁免只作用于 `brookesia_hal_custom`；另一处 IDF/Picolibc 属性拼写兼容只应用到上游一个 display 翻译单元，不放宽告警。

## CI 与独立环境准备

[Host-check workflow](../.github/workflows/host-check.yml) 与本地使用同一 `scripts/check.py`，CI 显式增加图检查；[Firmware-build workflow](../.github/workflows/firmware-build.yml) 独立执行 ESP-IDF 配置、Board Manager 生成和完整构建，不烧录设备。

没有物化依赖的 host-only checkout 可先安装与 ESP-IDF 6.0.1 相同的 Component Manager，再准备测试需要的锁定 Settings 与 Boost 组件：

```bash
python3 -m pip install idf-component-manager==3.0.3
python3 scripts/firmware/prepare_host_dependencies.py
python3 scripts/check.py
```

准备命令使用官方 Component Manager 从 dependencies.lock 获取组件并验证 hash；已有组件 hash 不匹配时失败，不覆盖本地改动。它只准备 host tests 的 Settings 资源与 Runtime JSON 编码所用 Boost，不解析或改写版本锁，也不替代固件依赖解析。统一检查本身仍只读，不隐式下载依赖。CI 的 GNU 编译器由 `CXX=g++` 选择；本地默认使用 clang++。
