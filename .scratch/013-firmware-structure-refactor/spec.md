# Firmware structure refactor

Sequence: 013

Status: active
Blocked by: None — baseline committed as 43159fb

## Problem Statement

ESPocket 的 ESP-IDF 工程已有清晰的 System、Shell、Native App 与 Runtime App 产品边界，但 `system.cpp` 和 `circular_shell.cpp` 正同时承载生命周期、导航、显示、输入、GUI 文档、状态刷新与阶段验证。Native 与 Runtime 资源目录的命名也未直接表达执行模型。继续堆叠会增加人和 AI 定位 Owner、评估影响范围及编写局部测试的成本。

本 Effort 在不改变产品行为的前提下收敛源码、资源、测试和构建依赖的职责。Home Space、PWR 与测试自动化的当前实现已固定于提交 `43159fb`，本 Effort 从该基线开始实施；尚未完成的产品功能与验收继续由各自 Effort 持有。

## Solution

以降低认知负担和提高修改局部性为首要目标。保留 `espocket_system`、`shell_circular` 与 Native App 现有 ESP-IDF component 边界，先在 component 内拆分私有实现、资源和测试；ESP-IDF 有明确约定时遵循其构建与目录语义，其余位置使用 ESPocket 自有约定。

结构重构必须保持现有导航、App lifecycle、PWR、Display State、Native/Runtime contract 与 AI Native Exposure Decision 不变。只有出现第二个真实 Adapter、独立生命周期或可替换实现时，才新增 component 或公开 Interface。

目标源码结构为：

```text
firmware/
├── CMakeLists.txt
├── dependencies.lock              # tracked dependency resolution
├── sdkconfig.defaults             # tracked product defaults
├── sdkconfig.defaults.m2-stress   # tracked validation profile
├── partitions_16m.csv             # tracked partition contract
├── main/
├── components/
│   ├── espocket_system/
│   ├── shell_circular/
│   └── gen_bmgr_codes/            # ignored Board Manager output
├── native_apps/
│   └── hello/
├── runtime_apps/
│   └── hello/
│       ├── build/                 # ignored toolkit output
│       ├── dist/                  # ignored release output
│       └── node_modules/          # ignored dependency materialization
├── compat/
├── managed_components/            # ignored Component Manager materialization
├── build/                         # ignored generated build tree
│   └── littlefs-root/             # generated root used to build littlefs_data
├── sdkconfig                      # ignored local resolved configuration
└── sdkconfig.old                  # ignored local configuration backup
```

`native_apps/` 中的每个子目录仍是 ESP-IDF component，由顶层 CMake 通过 `EXTRA_COMPONENT_DIRS` 发现。`components/` 表达系统级构建边界，两个 App 根目录表达产品执行模型。

`managed_components/` 不是 vendored source，也不是可编辑 Module；它由 `main/idf_component.yml` 与受控的 `dependencies.lock` 解析生成。上游变更通过版本约束、override 或 `compat/` 处理，不直接修改该目录。`gen_bmgr_codes/` 因 Board Manager 必须生成一个可发现 component 而留在 `components/`，但仍是忽略的生成物。

生成目录采用“可配置则归入 build tree，工具固定则留在原位”的规则。当前主机端 `firmware/littlefs/` 只是制作 `littlefs_data` 分区镜像前的文件系统根目录，迁移为 `firmware/build/littlefs-root/`；设备上的挂载点仍是 `/littlefs`，System Core 仍从 `/littlefs/apps` 加载 Runtime App。`managed_components/`、`components/gen_bmgr_codes/`、根目录 `sdkconfig` 及各 Runtime App 的 `build/`、`dist/`、`node_modules/` 使用各自工具的约定位置，不增加复制或同步层。

## User Stories

1. 作为维护者，我能从 component、公开头文件和少量职责明确的实现文件定位一项行为的 Owner。
2. 作为实现 agent，我能在不读取完整 Shell 或 System 巨型实现文件的情况下找到资源、导航、键盘、状态或生命周期代码及其测试。
3. 作为 reviewer，我能区分纯结构迁移与产品行为变化，并使用同一组验证确认重构没有改变可观察结果。

## Implementation Decisions

- 优先优化人和 AI 的代码导航、Owner 识别和修改局部性，不以目录外观或组件发布为首要目标。
- 首轮重构只移动和重组实现，不改变产品行为；发现的功能问题另开 ticket。
- ESP-IDF 有明确构建或测试约定时优先遵循 ESP-IDF；框架未规定的部分由 ESPocket 定义。
- `espocket_system` 与 `shell_circular` 保持为现有深 Module 和 ESP-IDF component；导航、显示、输入、键盘或状态不会仅因文件变大就成为独立 component。
- 当前功能改动先形成固定提交，结构重构在该基线上进行。
- Hello Native 与 Hello Runtime 是验证共同 App contract 的 Reference App；在仓库保留期间，它们进入正式固件、对用户可见并遵守完整产品契约。不再需要时明确删除，不转为长期隐藏资产。
- Component 自有断言统一放在 ESP-IDF 约定的 `test/`；跨 component 的固件断言放在 `firmware/test/`。
- Shell 与 Native App 的 GUI JSON 作为独立资源保存，并通过 ESP-IDF `EMBED_TXTFILES` 嵌入固件。
- 大型 Module 先保持同一个公开类和状态 Owner，将私有实现按职责拆到多个 `.cpp`；不为文件拆分预先创建 helper class。
- System 与 Shell 之间现有 callback 收敛为一个 `ShellHost` 参数对象，不引入只有一个实现的虚基类。
- `espocket::System` 直接消费 PowerKeyMonitor 事件并执行 Home；Shell 不再轮询 PWR 计数或转发 PWR Home。
- 每个 Shell 或 Native App 首先维护一个权威 `resources/gui.json`；不预先复制 Runtime App 的物理资源拆分。
- GUI action 继续在 JSON 和 C++ 中使用各自自然表达，由结构测试比较声明、订阅与 handler 集合，不建立代码生成器。
- `espocket_system/Kconfig.projbuild` 收敛为 component 自有 `Kconfig`。
- 公开头文件需要的依赖进入 `REQUIRES`；只有实现使用的依赖进入 `PRIV_REQUIRES`。
- `-Wno-error=attributes` 只应用到需要兼容的 `brookesia_hal_custom` target。
- 固件版本由 ESP-IDF `PROJECT_VER` 注入 `SystemInfo`；App manifest version 仍由各 App 自有。
- 可配置的 LittleFS 镜像根目录从 `firmware/littlefs/` 迁入 `firmware/build/littlefs-root/`；它是生成镜像的临时输入树，不是产品源码，设备挂载路径仍为 `/littlefs`。
- 工具固定或生态约定的生成路径保持原位：Board Manager 使用 `components/gen_bmgr_codes/`，IDF Component Manager 使用 `managed_components/`，ESP-IDF 本地配置使用根目录 `sdkconfig`，Runtime App 工具在各 App 内使用 `build/`、`dist/` 与 `node_modules/`。
- `managed_components/` 只由 IDF Component Manager 物化并视为只读；`dependencies.lock` 是受版本控制的解析结果，`main/idf_component.yml` 是依赖意图来源。
- `build/`、`sdkconfig`、`sdkconfig.old`、`managed_components/`、`components/gen_bmgr_codes/` 以及 Runtime App 的 `build/`、`dist/`、`node_modules/` 不纳入版本控制；统一检查验证这些边界，并在迁移后禁止重新引入根目录 `firmware/littlefs/`。
- 每个 `compat/` 文件记录受影响版本、上游问题与删除条件，并在依赖升级时复核。
- Runtime App 源码统一位于 `firmware/runtime_apps/<app>/`。
- ESPocket 自有 Native App 从通用 `components/` 抽离为一等 `firmware/native_apps/` 概念。
- `python3 scripts/check.py` 作为无需硬件的统一验证入口；固件构建、烧录与真机验收保持独立命令。
- Waveshare 1.75C 仍是唯一产品板；第二块板实际进入计划前不建立通用 Board component。
- `espocket_system/src/` 按启动装配、App lifecycle、导航、显示和 PWR 职责拆分；`shell_circular/src/` 按 IApp 生命周期、GUI document、Home gesture、keyboard 与状态刷新拆分。文件拆分不改变公开类或状态 Owner。
- `ShellHost` 只表达产品语义查询与命令，不暴露 GPIO、PWR 计数、LVGL 对象或 Service 实例。
- 本次不创建空的 `ESPocket App Navigator`；Page/Card contract 实施并形成真实状态不变量时，再在 `espocket_system` 内建立该 Module。
- Host 结构测试继续使用 Python 标准库 `unittest`；目标板组件行为测试使用 ESP-IDF Unity。
- `scripts/check.py` 只验证工作区，不自动修复、格式化或覆盖受控生成物；需要生成时使用临时目录比较。
- 文档 CI 收敛为统一 host-check workflow；完整 ESP-IDF build 使用独立 workflow。
- 本次不引入全量格式化；格式规范与存量格式清理另立 Effort。
- 迁移按测试入口、GUI 资源、Shell、System、构建元数据、CI 六个可独立验证阶段拆分 tickets 与 commits。
- 普通资源移动和文件拆分通过 host checks 与固件 build；PWR Owner、ShellHost 和导航路径完成后集中执行一次真机 smoke。
- 稳定目录规则写入 `firmware/README.md`，最终 Owner/Interface 写入架构文档，Reference App 写入 `CONTEXT.md`；本次不为可逆目录决定新增 ADR。
- ESPocket 自有普通、System 与 Reference Native App 位于 `firmware/native_apps/<app>/`，由 `EXTRA_COMPONENT_DIRS` 发现；Circular Shell 留在 `components/shell_circular`，上游 Settings 与 Store 留在 `managed_components`。
- 对称 Reference App 路径为 `native_apps/hello/` 与 `runtime_apps/hello/`；结构迁移保持现有 manifest ID 不变。
- 每个 Native App 自有 `CMakeLists.txt` 并显式声明 component 依赖；上游包版本暂由项目现有 `main/idf_component.yml` 统一解析，独立发布时再增加 App 自有 manifest。
- `espocket::System` 继续作为 Composition Root 显式安装内置 Native App；可以用私有 `install_builtin_apps()` 收拢顺序和错误处理，不引入静态自注册或生成 registry。
- Native 与 Runtime Reference App 保持独立实现，通过共同的行为测试和验收场景验证同一 contract；出现真实共享业务逻辑前不建立 DSL 或共享实现层。
- 本次结构调整不新增或改变 Semantic Registration；System、Shell、Service 与 App 继续在真实 Owner 边界作 Exposure Decision。

## Testing Decisions

- 结构迁移前后必须使用同一组静态检查、组件测试、固件构建与适用的既有验收结果进行比较。
- 测试可以分析源码或资源，也可以执行组件行为；这些断言按 Owner 放入 component `test/` 或跨组件 `firmware/test/`。
- Host 上可确定执行的检查由 `python3 scripts/check.py` 统一编排；ESP-IDF build 和需要设备的验证使用独立入口并分别报告结果。
- 重构不得通过删除断言、降低编译告警或跳过现有验证来获得通过。

## Out of Scope

- 改变 Home、Back、App Page 栈、App Card、PWR、Screen Off 或 wake 的产品语义。
- 为假设中的第二块开发板预先设计抽象层。
- 将每个私有职责拆成独立 ESP-IDF component。
- 修改 Brookesia managed components 或建立第二套 Native/Runtime lifecycle。
- 新建集中式 AI Manager；AI Native 仍在真实 Owner 边界作 Exposure Decision。
- 仅为统一目录外观而改造 Board Manager、LittleFS 或 ESP-IDF 的生成链。

## Tickets

1. [统一 host checks 与测试位置](issues/01-unify-host-checks-and-test-placement.md)
2. [抽离并验证 GUI 资源](issues/02-extract-and-verify-gui-resources.md)
3. [拆分 Circular Shell 并收敛 ShellHost](issues/03-split-circular-shell-and-shell-host.md)
4. [拆分 System 并收回 PWR Owner](issues/04-split-system-and-own-power-input.md)
5. [收敛源码、构建与生成目录](issues/05-normalize-source-build-and-generated-layout.md)
6. [收敛 CI 并完成最终验证](issues/06-converge-ci-and-final-verification.md)

## Further Notes

- [统一语言](../../CONTEXT.md)
- [核心 Module 协作](../../docs/design/architecture/03-core-modules.md)
- [启动与生命周期](../../docs/design/architecture/04-boot-lifecycle.md)
- [导航与应用运行](../../docs/design/architecture/05-navigation-runtime.md)
- [ADR-0003：Native 与 Runtime 共享 System Core contract](../../docs/adr/0003-native-and-runtime-share-the-system-core-contract.md)
- [ADR-0009：AI Native 是基础设计维度](../../docs/adr/0009-ai-native-is-a-foundational-design-dimension.md)

`Reference App` 已同步到 `CONTEXT.md`；Native/Runtime 源码和当前 Owner 目录规则见 `firmware/README.md`。

## Execution Notes

- 2026-10-02：用户要求提交当前代码并开始本 Effort；固定基线 `43159fb`，先执行 01。基线已有真实 `espocket_navigation` 状态 Owner，结构调整保留其 component 边界，不另建 Navigator。

- 2026-10-02：01 已完成，统一 host checks 与完整构建通过；结果见 [阶段记录](records/2026-10-02-host-checks.md)。下一执行 frontier 为 02 GUI 资源抽离。

- 2026-10-02：02 已完成，GUI 资源与 manifest 比对一致，Host checks 和完整构建通过；见 [阶段记录](records/2026-10-02-gui-resources.md)。下一执行 frontier 为 03 Shell 拆分与 ShellHost。

- 2026-10-02：03 完成 Shell 拆分及 ShellHost，Host checks 和构建通过；见 [阶段记录](records/2026-10-02-shell-split.md)。

- 2026-10-02：04 源码、Owner 断言及构建完成，真机 smoke 留到 05/06 最终镜像集中执行；[阶段记录](records/2026-10-02-system-split.md)。05 的纯目录整理先继续，不提前关闭 04 真机条件。

- 2026-10-02：05 完成目录、依赖、Kconfig、版本与 LittleFS build 输入收敛；Host checks、完整重编译通过，见 [阶段记录](records/2026-10-02-layout-build.md)。

- 2026-10-02：06 的 CI 与文档收尾、最终自动验证完成；已刷入重构镜像并核对 USB identity，04/06 等待一次集中 smoke 结果，见 [最终验证记录](records/2026-10-02-final-verification.md)。

- 2026-10-02：用户授权睡眠期间继续检查与执行剩余 issues。04/06 人工条件保留，独立源码 frontier 与晨间最小介入见 [夜间执行记录](records/2026-10-02-overnight-frontier.md)。
