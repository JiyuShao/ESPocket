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

产物位于 `<workspace>/firmware/build/`，配置位于 `<workspace>/firmware/sdkconfig`，输入身份位于 `<workspace>/patch-inputs.json`。生成的 lock 只属于此次构建；registry lock 与补丁 manifest 共同限定产品输入。`--prepare-only` 只准备副本，不构建也不证明设备修复。默认 `--patch-set production` 使用已验收的 Runtime/Core/HAL/Settings/Display/Board Manager 补丁及 playback-only 配置；`--patch-set hal-candidate` 显式试做 HTTP/Audio HAL 候选（普通配置不打开 Audio Processor）；`--patch-set audio-candidate` 另外固定 playback-only 的新增依赖、开启 Player/Processor/Audio Service，并强制 Recorder/AFE/Media Dump/Video 关闭。Audio 候选在 reconfigure 后复核这些选项与精确版本/hash，再构建；实验依赖不改生产 lock。候选不等于设备门槛通过。升级源码/hash 不匹配时停止，不能绕过校验。

产品构建将指令与只读数据留在 Flash，关闭 `SPIRAM_XIP_FROM_PSRAM`、`SPIRAM_FETCH_INSTRUCTIONS` 与 `SPIRAM_RODATA`。此板默认的指令搬运会占用约 5 MiB PSRAM，压缩 Runtime GUI、JS 编译与包解压空间。独立构建入口会纠正旧 sdkconfig 并复核配置；Flash 操作仍由 cache-safe Storage worker 执行，线程栈预算保持既有配置。对应原包和设备结果见 [Runtime / Store 回归票](../.scratch/005-m5-application-ecosystem/issues/11-runtime-store-gesture-regressions.md)。

产品入口使用性能优化编译、32 MiB Flash 和 `partitions_32m.csv`：App 位于 `0x60000`，预算 14 MiB；LittleFS 位于 `0xe60000`，预算 17.625 MiB。新增 NES 与 Agent 依赖的版本/hash 由 `store-app-dependencies.json` 固定，真实服务自动注册；AI 在线功能仍需要对应服务的激活或凭据。加载的 sdkconfig 必须来自完整的板级配置，不能使用关闭 Display/Network/System HAL 的旧缓存配置。产品 DisplaySource 显式使用 24 行双内部缓冲，每块 22,368 bytes，保留启动 Wi-Fi 所需的内部 RAM；32 行配置虽能显示，实际导致 Wi-Fi RX buffer 分配失败。上游／构建候选的默认 40 行值仍保留，实际产品配置以此处的 Owner 装配为准。

产品独立构建同时将准确匹配的生成 SPI display `max_transfer_sz` 配为 29,824 bytes。未声明支持 ESPocket 的 Runtime 使用圆内 329px 安全 viewport 和 480dp 逻辑画布；固定 800×480dp 布局的官方 AI Chatbot 0.2.1 使用 329×197px 居中横向 viewport，使设置和 Agent 选择入口可操作；原始 BPK 不改写。产品主题补齐官方 App 的共享控件样式，启用 Montserrat 10/12/14/16；中文字体按字号使用 96/48/16 字形缓存。这些内存预算与 512 KiB 图片缓存独立。Launcher 使用每页四行的 Release 翻页，减少连续软件重绘。测量结果与启动性能限制由 [存储与圆屏验收记录](../.scratch/005-m5-application-ecosystem/records/2026-10-06-storage-round-runtime.md)和 [小智／Launcher 工作票](../.scratch/005-m5-application-ecosystem/issues/13-xiaozhi-and-launcher-performance.md)持有。

已有设备从旧分区迁移前，先完整备份旧 Flash 并保留启动、NVS、App、LittleFS 回滚区域。用具有 littlefs-python 的 Python 执行 `scripts/firmware/migrate_littlefs.py --backup <old-littlefs.bin> --output <new-image.bin> --size 0x11a0000`，核对逐文件摘要后，将迁移镜像写入新 LittleFS 地址；同次部署匹配的 bootloader、partition table 和 App，保留 NVS/model。迁移工具只生成镜像，不烧录；它作废 Core 持久验证记录，使首次启动重新完整验证安装包。部署迁移设备时，不能使用构建生成的全新 `littlefs_data.bin` 覆盖已有文件。挂载失败自动格式化已关闭。

Store 成功提交安装后回收自有下载副本，Core 的安装原包和用户 data/files 保留。下载包缓存目标为 512 KiB，优先清理已安装版本和旧版本，再按修改时间回收；单次最多处理 64 个候选，正在下载、待确认或排队安装的包保留。扫描清理自有中断 `.bpk.part`，手动导入包不参与回收。下载与 Core 安装分别读取实际可用容量，预算包括候选原包、解包、更新保留文件和分配开销；容量未知或不足时提前失败，失败安装保留旧版本。图像缓存与磁盘包缓存的预算独立。

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

没有物化依赖的 host-only checkout 可先安装与 ESP-IDF 6.0.1 相同的 Component Manager，再准备测试实际读取的锁定组件源码：

```bash
python3 -m pip install idf-component-manager==3.0.3
python3 scripts/firmware/prepare_host_dependencies.py
python3 scripts/check.py
```

准备命令使用官方 Component Manager 从 dependencies.lock 获取组件并验证 hash；已有组件 hash 不匹配时失败，不覆盖本地改动。它只物化 host tests 实际读取的组件（包括 Settings／Store、Core、GUI、HAL、Storage、HTTP、Display、Utils、Board Manager、PNG decoder、Boost 与 LVGL），逐个核对 lock 中的 hash；不改写版本锁，也不替代固件依赖解析。统一检查本身仍只读，不隐式下载依赖。CI 的 GNU 编译器由 `CXX=g++` 选择；本地默认使用 clang++。

Runtime 异步确认故障最小设备回归使用 `--suite runtime-confirm`，与其他套件共用设备身份、镜像核对和失败报告规则。此套件通过不代表完整 App 契约验收；上游阻塞与诊断见[Runtime 异步 GUI 栈溢出](../.scratch/008-m8-app-contract/records/2026-10-02-runtime-js-async-stack-overflow.md)。

Audio 候选当前使用 466px 板的 40 行双缓冲配置，并将官方 simple-player 输出转换为锁定 DAC 的 16 kHz、双声道、16 bit，构建校验拒绝输出格式漂移；默认 production 构建也使用已验收的 playback-only 配置，Recorder/AFE 关闭。启动内存测量与验收见 [Audio 记录](../.scratch/004-m4-device-capabilities/records/2026-10-03-playback-only-patch.md)。

系统级 App 样式由 [Product GUI themes](components/espocket_system/resources/README.md) 在启动时注册；布局缺失与圆屏裁切状态见 [004/05](../.scratch/004-m4-device-capabilities/issues/05-fix-settings-controls-rendering.md)。

### Audio playback hearing fixture

[Audio probe preparer](../scripts/firmware/prepare_audio_playback_probe.py) 仅接受 checkout 外的既有 audio-candidate，校验 Recorder/AFE 关闭且 Adapter/CMake 未加探针，再装配 [临时 Native fixture](test/device/fixtures/audio_playback_probe.hpp)。显式运行 `python3 scripts/firmware/prepare_audio_playback_probe.py --project <workspace>/firmware` 后构建并记录新的 image identity；普通构建不包含该 fixture。

进入官方 Settings Sound 后，fixture 使用每次装配生成并记录的唯一测试路径，通过官方 Storage Service 检查路径不存在，再写入自己的测试 WAV，调用官方 AudioPlayback Play（400 Hz 间歇短音、30 次循环，配置 35 秒播放超时；实际总时长受播放器处理影响）；音量与 Mute 继续由真实 Settings/Audio Owner 调整，probe 不改它们，也不提供 Assistant/USB 播放入口。Back 或 PWR Home 调用官方 Stop 后通过 Storage Service 删除已确认由本次创建的文件；同名未知文件阻止测试，不覆盖或删除。检查与写入依赖当前串行的单一 fixture，不承诺通用并发文件创建原子性。实际听感需一次人工确认，自动 Owner state 与日志不能替代。验收后恢复已保存、不含 probe 的镜像。

Probe 的 Flash IO 必须交给 Storage Service 内部 RAM 工作线程；Native App 回调可能使用外部 RAM 栈，不能直接 open/write/remove Flash 文件。真实 fixture 的主机回归验证 Storage/Audio 所有权、拒绝已有数据及失败清理；实际 cache-safe 与播放仍以设备结果为准。

### Settings 亮度压力回归

概率性 Display IO 缺陷使用专门的自动套件，不增加人工 smoke 次数：

```sh
python3 scripts/firmware/run_device_tests.py --suite settings-brightness \
  --port /dev/cu.usbmodem101 --device-id A0:F2:62:E3:0B:68 \
  --expected-image <exact-image-identity> --output /private/tmp/espocket-brightness-stress
```

使用有 pyserial 的 IDF Python。466px profile 当前自动拖动 100 次（旧基线第 60 次失败），每次必须命中真实亮度 Owner，任何 timeout 即失败；末尾验证 Back 与 Home。此套件不操作主题、不验证物理触摸或像素。候选 `display-candidate` 继承 audio-candidate 并在独立副本中加上 Display 输出 IO 补丁；默认 production 组合现包含已验收 Display 补丁；原最小组合可显式选 baseline。

### Audio teardown 自动回归

`--suite audio-playback` 仅用于显式加入上述 Audio probe 的独立测试镜像；普通固件不会自动播放短音。用真实 Owner Playing 与 Home 删除其自有 WAV 验证两次播放/退出/再打开，并拒绝 I2S 重复 disable；它不代替听感验收。测试完成后恢复不含 probe 的默认生产镜像。


### Runtime 键盘隔离夹具

`firmware/test/device/fixtures/keyboard_isolation/` 包含两个隐藏 Runtime 观察者、一个真实键盘 Owner 与临时 Native 协调器。观察者订阅 KeyboardClosed/Display.BacklightBrightnessChanged 并运行定时器，正常与故意抛错的 on_stop 均不主动清理；真实 Core 必须完成资源撤销。Owner 只校验固定的合成输入，不打印事件正文。Native 协调器通过真实 Core 生命周期 API 启动和停止观察者；Runtime 无权启动其他 App 的规则保持。

先备份设备当前 LittleFS 与普通固件。使用具有 littlefs-python 的构建环境执行 `scripts/firmware/prepare_keyboard_isolation_fixture.py --backup <backup.bin> --output <new-test-image.bin> --project <isolated-workspace>/firmware`，再构建此独立测试工程。输出路径必须新建且在 checkout 外；原文件 inventory 与测试变更 hash 写入同名 JSON。部署测试固件和对应文件系统后，用 IDF Python 执行 `scripts/firmware/run_keyboard_isolation_probe.py --port <port> --device-id <inventory-id> --expected-image <exact-identity> --output <new-report-directory>`。它复用 USB 客户端与 Owner 状态断言，不增加测试协议或生产权限。

测试后恢复普通固件和备份的文件系统；不删除未知目录或文件，不修改 NVS，不解除 failed-stop keyboard latch。此夹具不宣称签名包安装、上架、真实触摸或正常固件的物理键验收。


### Store 请求容量候选

production 已包含 Store 0.8.2 的图标容量延后重试；`--patch-set store-candidate` 保留为同一基线的显式入口。HTTP 使用 2 workers / 1 request：下载占用一个 worker 时，另一个仍能发布周期进度；单请求限制继续避免 TLS 分配重叠。TLS 验证、包兼容性与信任判断保持启用。设备刷新及退出门槛由 [005/06](../.scratch/005-m5-application-ecosystem/issues/06-adopt-online-store-stability-fix.md) 持有；下载进度复验由 [005/11](../.scratch/005-m5-application-ecosystem/issues/11-runtime-store-gesture-regressions.md) 持有。候选通过 host 回归不代表安装链路可用。

### 内置字体字形门槛

`python3 scripts/firmware/check_glyphs.py` 检查维护 JSON 的 literal label 是否由实际选定内置字体覆盖；有效固件配置可通过 `--sdkconfig` 指定。它已接入 host tests 与独立补丁构建的 reconfigure 后检查。范围与图标开发规则见 [资源说明](components/espocket_system/resources/README.md#内置字体与图标检查)。

### Store 在线回归与签名测试输入

`run_device_tests.py --suite store-online` 在普通候选固件上打开 Store、点击 Refresh，要求本次远程 index 真正写入缓存，再验证 Home 和重进。缓存启动不能独自满足这个门槛；此 suite 不安装或下载包，不证明信任、回滚与发布。

安装链路的独立签名测试输入见 [Store release fixture](test/fixtures/store_release/README.md)。官方 SDK 生成两个兼容版本，输出到仓库外的新目录；临时测试 identity 不进入正式信任策略。

### Runtime 绘制诊断与解码缓存

`CONFIG_ESPOCKET_RUNTIME_RENDER_PROFILE` 默认关闭；开启后，每约两秒聚合 Runtime PNG decoder open（实际 cache miss／无缓存解码）、成功次数与耗时、LVGL render 耗时及 adapter 最近一秒完整末次 flush 完成 FPS。统计从 `on_app_started` 开始，不能覆盖此前 `on_start` 的全部启动解码。GUI 线程经单元素有界队列交给独立诊断线程输出，慢串口可能覆盖待输出窗口；截断日志和窗口边界不作为有效样本。Core 的 `CONFIG_BROOKESIA_SYSTEM_CORE_ENABLE_PROFILE_LOG` 另记录 periodic timer 的调度唤醒、Owner 排队、回调和实际 dispatch 周期。

`CONFIG_ESPOCKET_RUNTIME_IMAGE_CACHE_BYTES` 设置共享 LVGL decoded image cache 的字节预算，默认 512 KiB，最多 2 MiB；它不是预分配，也不包含正在绘制的缓冲、decoder 临时工作区和缓存管理开销。decoder allocator 保持上游配置。超预算图像绕过缓存；PNG 解码前若 PSRAM 最大连续块不足以承载 RGBA 缓冲，或总空闲不足以额外保留 64 KiB 临时工作区，则先清掉缓存。`pressure_evictions` 计数清缓存请求，不能保证基础堆自身仍能分配成功。资源替换／释放使用 GUI backend 的 `lv_image_cache_drop`。该 fallback 与诊断开关独立，且共享缓存也影响 Native 图像。预算不能按 App PNG 文件解码总量直接决定；必须比较同机原包的成功解码、完整绘制、timer 和 PSRAM free/largest，出现缺图时 FPS 增加不算性能收益。截图使用逐行无损 RLE／raw 存储，避免要求连续整帧缓冲；捕获期间清空并暂停 decoded image cache，结束后恢复实际预算。早期 1 MiB 试验的连续整帧分配失败仍保留为历史结果；512 KiB 已通过原包性能、70 秒前台压力、五图截图和完整 Apps 联合回归；更大预算仍须独立验收。下载后须立即 `release`，并在性能窗口外截图。当前试验与镜像结果由 [005/10](../.scratch/005-m5-application-ecosystem/issues/10-reduce-runtime-startup-blocking.md) 持有。
