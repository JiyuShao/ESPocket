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

## 已接受源码补丁的产品构建

Runtime JS 0.8.3 的栈配置补丁依据 [ADR-0015](../docs/adr/0015-runtime-async-stack-patch-exception.md)维护；Core 0.8.4 的键盘 Owner 与退出清理补丁依据 [ADR-0016](../docs/adr/0016-maintained-upstream-fixes.md)维护。上面的直接 idf.py 命令用于物化上游依赖与生成板级配置，直接构建不会应用这些补丁。产品镜像使用独立入口：

```bash
python3 scripts/firmware/build_patched_firmware.py \
  --workspace /tmp/espocket-patched-build \
  --sdkconfig firmware/sdkconfig
```

先加载 ESP-IDF 环境。workspace 必须不存在且位于源码 checkout 外；每次独立构建保留各自证据。入口复制工程和已物化依赖，准确应用 hash 锁定补丁，使用 Component Manager override_path 选择副本，再执行完整构建并核对选中的组件路径。原始 managed_components、sdkconfig 和 dependencies.lock 不写入。工程副本把全部 Registry 版本约束为原始 lock 的精确版本，构建后核对版本和 component hash，阻止切换 override 时顺带升级传递依赖。当前产品预算为 16 KiB，上游默认仍为 8 KiB。

产物位于 `<workspace>/firmware/build/`，配置位于 `<workspace>/firmware/sdkconfig`，输入身份位于 `<workspace>/patch-inputs.json`。生成的 lock 只属于此次构建；registry lock 与补丁 manifest 共同限定产品输入。`--prepare-only` 只准备副本，不构建也不证明设备修复。默认 `--patch-set production` 使用已接入的 Runtime/Core 补丁；`--patch-set hal-candidate` 显式试做 HTTP/Audio HAL 候选（普通配置不打开 Audio Processor）；`--patch-set audio-candidate` 另外固定 playback-only 的新增依赖、开启 Player/Processor/Audio Service，并强制 Recorder/AFE/Media Dump/Video 关闭。Audio 候选在 reconfigure 后复核这些选项与精确版本/hash，再构建；实验依赖不改生产 lock。候选不等于设备门槛通过。升级源码/hash 不匹配时停止，不能绕过校验。

## 测试

只约束一个组件、Native App 或 Runtime App 的测试放在该 Owner 的 `test/`；跨模块主机测试放在 `firmware/test/host/`，真实设备测试放在 `firmware/test/device/`。测试可以执行组件行为，也可以分析源码或资源，只要它对稳定约束做出可重复的断言。

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

## 测试目录与职责

先按行为的 Owner 定位测试，再按执行环境选择入口。组件自身的单元、契约和 Adapter 兼容测试共用该组件的 `test/`；不按测试语言或文件数量新建目录。App 资源、动作和 JS 生命周期测试放在各自 App 的 `test/`。跨模块集成、仓库布局与测试执行器的离线测试放在 `firmware/test/host/`。

```text
firmware/
├── components/<owner>/test/
├── native_apps/<app>/test/
├── runtime_apps/<app>/test/
└── test/
    ├── host/
    └── device/
        ├── e2e/       # navigation.py、cards.py：真实设备用户路径
        ├── support/   # USB 客户端、状态断言、attempt 与失败清理
        └── profiles/  # 设备布局的坐标、手势与校准信息
```

`scripts/check.py` 显式发现各 Owner 的 `test/` 和 `firmware/test/host/`，不发现 `device/`，不打开串口、不刷写、不改变开发者模式。设备测试通过 `scripts/firmware/run_device_tests.py` 显式运行；`--suite navigation`（默认）、`--suite cards`、`--suite surfaces` 与 `--suite apps` 选择用例；surfaces 补查普通配置的 Card 边界、系统页面 PWR Home、Quick Settings → Settings 与 App 普通横滑；apps 在普通配置验证 Native/Runtime 导航、待决 Back 与未回收息屏恢复。`--suite runtime-confirm` 为异步确认反馈最小回归；`--suite reclaim-native` / `reclaim-runtime` 分别要求只开启对应模型回收配置，验证目标回收与另一模型未回收恢复。`--suite resources` 在关闭回收、开启资源诊断的镜像执行三轮有限 App 路径与表盘 heap/stack checkpoint；报告中的语义路径通过不自动判定内存稳定，需核对串口采样。当前资源与回收使用同一设备目录，不增加另一套 USB 协议。

USB 客户端只负责线缆协议、响应匹配和快照校验；执行器负责行为断言、步骤、attempt 及始终执行的清理；E2E 用例调用执行器，不自行实现串口协议或另一份导航状态。CLI 负责参数、连接和产物目录。

人工画面、真实触摸和实体键验收步骤放在相应 ticket；有日期的判定和 identity 放在同一 Effort 的 records。原始报告与日志保留在 `--output` 指定的本地目录或 CI artifacts，不提交源码。当前默认临时目录保持 `/private/tmp/espocket-interaction`。

旧 `scripts/firmware/interaction_driver.py` 只转发到新 CLI；旧 profile 路径通过符号链接指向唯一的 `device/profiles/circular-466.json`。已有命令参数与报告字段保持不变，新文档使用新入口与配置位置。

## USB 合成输入回归

启用设备开发者模式并刷入具有 touch/PWR/snapshot/release capability 的固件后，使用 [run_device_tests.py](../scripts/firmware/run_device_tests.py) 执行单次自动路径。它不自动刷写、重启或开启模式；需要 `pyserial`，可使用 ESP-IDF Python 环境。必须显式指定设备清单 ID 和期望镜像 identity。CLI、466px profile 与报告格式见 [交互测试协议](../docs/development/interaction-test-protocol.md)。输出仅证明 `synthetic-input`，不能满足 GPIO、触摸硬件或视觉条件。

## Card 样例测试镜像

`CONFIG_ESPOCKET_M8_CARD_SAMPLE_TEST` 默认关闭。测试配置开启后，设备必须已持久开启 Developer Mode，且恢复后的 Card 配置为空；框架才使用临时左右序列：左侧 Native summary/detail，右侧 Runtime summary/detail。有既有配置或恢复失败时不替换。临时配置只在 RAM 中，不由卸载或声明更新写回 NVS；System 重启先释放临时配置再恢复存储。显式调用 `configure_cards` 成功后才转为用户持久配置。它是验收 fixture，不是 Card 编辑器。

从 Watch Face 向右滑进入 Native summary，再向右滑进入 Native detail；向左滑进入 Runtime summary，再向左滑进入 Runtime detail。每张 Card 的 Open App/Open Detail 打开对应完整 App；Detail Back 回 Root、Root 无 Back，PWR Home 回 Watch Face。向内横滑逐张返回，首张回 Watch Face；息屏后再显示应重新请求数据。每条物理路径集中一次，合成输入与视觉/GPIO 证据分别记录，仍不能替代尚待回应的 013 smoke。

## 独立 App 回收测试

`CONFIG_ESPOCKET_M8_RECLAIM_NATIVE_TEST` 与 `CONFIG_ESPOCKET_M8_RECLAIM_RUNTIME_TEST` 默认关闭，可分别在测试配置中开启。自动息屏后，只停止所选执行模型的可见 resume target；另一模型保持原 Page。两个开关均开时覆盖两类，旧 `CONFIG_ESPOCKET_M6_RECLAIM_ON_TIMEOUT_TEST` 仍覆盖两类。它们复用真实 Core stop、Navigator 失效及键盘/临时 GUI 清理，不增加 USB 命令或内存淘汰策略。日志 `APP_RECLAIM_TEST` 包含 model、manifest 与 App ID；旧 M6 开关保留原事件。唤醒应到 Watch Face，用户重新打开从 Root 开始。此处为源码入口，物理和视觉验证由 008/03 持有。

## GUI 资源

Circular Shell 与 Hello Native 以 `resources/gui.json` 为完整 App/Shell 的 GUI 文档源码；Hello Native 的独立 Card 文档另存 `resources/card.json`。CMake 在构建目录生成 `shell_gui.json`／`hello_gui.json`／`hello_card.json` 副本，再用 `EMBED_TXTFILES` 嵌入；不同文件名避免 ESP-IDF 按 basename 生成的符号重名。生成副本不编辑、不提交，资源变化会触发重新配置与嵌入。

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
- [`compat/`](compat/README.md) 保存自有兼容实现与编译适配；每个文件记录影响版本、上游问题和删除条件。当前 attributes 告警豁免只作用于 `brookesia_hal_custom`；另一处 IDF/Picolibc 属性拼写兼容只应用到上游一个 display 翻译单元，不放宽告警。

- [`patches/`](patches/README.md) 保存已接受的上游源码 diff 与版本/应用顺序元数据，构建副本不提交；产品构建入口准确应用 Runtime 栈配置与 Core 键盘隔离补丁，设备验收状态见对应工作票。compat 与 patches 分开，核查与故障材料归[对应 Effort](../.scratch/README.md) 的 records。

## CI 与独立环境准备

[Host-check workflow](../.github/workflows/host-check.yml) 与本地使用同一 `scripts/check.py`，CI 显式增加图检查；[Firmware-build workflow](../.github/workflows/firmware-build.yml) 独立执行 ESP-IDF 配置、Board Manager 生成和完整构建，不烧录设备。

没有物化依赖的 host-only checkout 可先安装与 ESP-IDF 6.0.1 相同的 Component Manager，再准备测试需要的锁定 Settings 与 Boost 组件：

```bash
python3 -m pip install idf-component-manager==3.0.3
python3 scripts/firmware/prepare_host_dependencies.py
python3 scripts/check.py
```

准备命令使用官方 Component Manager 从 dependencies.lock 获取组件并验证 hash；已有组件 hash 不匹配时失败，不覆盖本地改动。它只准备 host tests 的 Settings 资源与 Runtime JSON 编码所用 Boost，不解析或改写版本锁，也不替代固件依赖解析。统一检查本身仍只读，不隐式下载依赖。CI 的 GNU 编译器由 `CXX=g++` 选择；本地默认使用 clang++。

Runtime 异步确认故障最小设备回归使用 `--suite runtime-confirm`，与其他套件共用设备身份、镜像核对和失败报告规则。此套件通过不代表完整 App 契约验收；上游阻塞与诊断见[Runtime 异步 GUI 栈溢出](../.scratch/008-m8-app-contract/records/2026-10-02-runtime-js-async-stack-overflow.md)。

Audio 候选当前使用 466px 板的 40 行双缓冲配置；普通生产配置不变。启动内存测量与验收见 [Audio 记录](../.scratch/004-m4-device-capabilities/records/2026-10-03-playback-only-patch.md)。

系统级 App 样式由 [Product GUI themes](components/espocket_system/resources/README.md) 在启动时注册；布局缺失与圆屏裁切状态见 [004/05](../.scratch/004-m4-device-capabilities/issues/05-fix-settings-controls-rendering.md)。
