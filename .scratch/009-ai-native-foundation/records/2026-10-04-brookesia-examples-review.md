# ESP-Brookesia 0.8 examples 迁移核查 — 2026-10-04

本记录保存一次官方源码调查及迁移候选评估，不改变任务状态，不代表依赖升级、构建或真机验收。长期设计仍由 ESPocket 的 Context、ADR 和产品契约持有。

## 源码边界

调查源为官方 `espressif/esp-brookesia`，2026-10-04 获取的 `master` HEAD：`e937455b0db1a3e873b1da61d6d13652f3dcc7e2`；浅克隆只读副本保存在 `/tmp/espocket-brookesia-review-20261004`。以下链接均固定到该提交。官方 [版本说明](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/README.md) 将 master 标为 v0.8 active development，除 ESP32-S31 外支持 IDF >= 6.0、<= 6.2；这是开发线快照，不是统一发布的 0.8 补丁版本。

`examples/` 下共有七个独立示例：`agent/chatbot`、`system/super`、`service/audio`、`service/console`、`service/http`、`service/storage`、`service/wifi`。该快照没有 ESP-Claw 示例；不能从 XiaoZhi/Coze/OpenAI 示例推断 ESP-Claw 已受支持。目录证据见[固定提交 examples 树](https://github.com/espressif/esp-brookesia/tree/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples)。

各示例 manifest 引用 `0.8.*` 并用 `override_path` 指向同一仓库源码。因此示例能编译并不证明与 ESPocket 的精确锁定 Registry 包兼容；逐组件接口和 transitive dependencies 需另做核对。

## 七个示例与迁移价值

| 示例 | 源码确认的功能和关键入口 | 对 ESPocket 的增量判断 |
|---|---|---|
| Chatbot | 多 provider、唤醒/VAD、表情、设置切换、Wi-Fi 配网、MCP、profiling。[README](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/agent/chatbot/README.md)；[ai_agents.cpp](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/agent/chatbot/main/modules/ai_agents.cpp)；[manifest](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/agent/chatbot/main/idf_component.yml) | **高价值，需要先设计**：复用 Agent Manager/provider 生命周期、文本和语音事件、XiaoZhi MCP 注册；Assistant 界面、User Intent、权限、Owner 和 Home 取消由本项目持有。不要复制其整套 main、Display、Settings 或常驻 chatbot 产品形态。 |
| HTTP | 同步/异步 request、request_id 查询、取消、retry、状态/进度/终态事件、TLS 三模式、headers、下载与 BodyTooLarge 验证。[README](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/http/README.md)；[main.cpp](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/http/main/main.cpp)；[manifest](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/http/main/idf_component.yml) | **高价值，可提取回归场景**：对应 005/06 Store 稳定性验证，提取 EventCollector 与终态关联方式。示例不是 Store 修复证明；其 Apifox 网络条件、取消竞争和 TLS Skip 演示不能直接成为生产策略。 |
| Wi-Fi | RAII 订阅、扫描、连接/断开、重启自动重连、SoftAP 配网、清凭据。[README](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/wifi/README.md)；[main.cpp](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/wifi/main/main.cpp)；[manifest](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/wifi/main/idf_component.yml) | **高价值，可提取配网增量**：已有 Wi-Fi Service owner 可以沿用，补手机配网入口、成功/取消/超时处理和屏幕反馈；扫描和基本连接无需重做。重置凭据 demo 不应自动进入正常启动流程。 |
| Console | svc_list/funcs/events/call、订阅和 binding 释放，debug_mem/thread/time，Flash 历史。[README](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/console/README.md)；[cmd_service.cpp](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/console/components/cmd_service/cmd_service.cpp)；[manifest](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/console/main/idf_component.yml) | **中价值，开发工具限定**：先引入只读 introspection、thread/time profiling；必须纳入现有开发模式和 USB transport 规则。通用 svc_call 能直接实施副作用，不能直接作为 Assistant 或生产入口。 |
| Audio | 单/多 URL 播放、队列 append/interrupt、loop、暂停恢复停止、PCM/OPUS/G711A 麦克风 loopback、AFE/VAD/WakeNet。[README](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/audio/README.md)；[main.cpp](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/audio/main/main.cpp)；[manifest](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/audio/main/idf_component.yml) | **分阶段价值**：播放控制事件可补已有播放回归；recorder/codec loopback/AFE 应成为独立语音硬件验收前置。当前 playback-only 不足以承诺 Chatbot，不能直接开启 Recorder/AFE。 |
| Storage | KVSet/Get/List/Erase、type-safe save/get、整数浮点vector/struct序列化、namespace隔离、缺键/类型错误。[README](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/storage/README.md)；[main.cpp](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/storage/main/main.cpp)；[manifest](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/service/storage/main/idf_component.yml) | **较低增量**：项目已有 Storage/NVS 和 Settings，作为类型与隔离回归参考；Card config 当前仍直接调用 NVS，可后续评估迁至 Storage helper，保持既有 namespace/key/data 可读与失败语义。后续 provider 配置可沿 owner 使用 type-safe API，避免再建配置存储。示例不是凭据安全存储设计。 |
| System Super | HAL/services + GUI/Runtime/System 装配，Settings/Store/Files，NES及Coze/XiaoZhi依赖，资源 staging、USB console/host pairing、编译优化。[README](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/system/super/README.md)；[main.cpp](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/system/super/main/main.cpp)；[manifest](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/system/super/main/idf_component.yml) | **装配已有覆盖，工具可提取**：不替换 ESPocket System/Shell、导航、Runtime。Files 可作未来独立 App 候选；NES/Video 等以产品需求决定。构建分析与编译并行限制可单独评估。 |

## Chatbot 需要拆开的部分

[生命周期处理](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/agent/chatbot/main/modules/ai_agents.cpp#L378-L474) 通过 AgentManager helper 订阅终态与 suspend、设置 target、Activate/Start/Stop；[会话事件](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/agent/chatbot/main/modules/ai_agents.cpp#L749-L871) 订阅 speaking/listening 和用户/Agent 文本，适合映射到 ESPocket Assistant 呈现。[Manager InterruptSpeaking](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/service/agent/brookesia_agent_manager/include/brookesia/agent_manager/manager.hpp#L179) 表明 provider 打断已有框架接口；它不能替代本项目语义调用的取消与提交边界。

[MCP Service tools](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/agent/chatbot/main/modules/ai_agents.cpp#L254-L301) 先读取 Device capabilities，再按 Battery/Camera capability 选择 Service functions；[custom Camera tools](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/agent/chatbot/main/modules/ai_agents.cpp#L1248-L1315) 使用 CustomTool callback 注册 Camera Open/Close/TakePhoto。可借鉴能力存在检查、tool schema 和 callback 接法，但 capability 筛选只是可用性检查，不是授权；示例还导出 SetPowerBatteryChargingEnabled，不能照搬电池充电或相机原始权限。README 声称亮度/音量 MCP 控制；本次 main/modules 源码检索未发现对应显式注册，因此不能把 camera callback 当成现成亮度 semantic adapter，实际默认工具路径仍需沿依赖继续核对。

[Wi-Fi provisioning module](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/agent/chatbot/main/modules/wifi_provisioning.cpp) 使用 Service binding 与 scheduler：有保存 AP 则 STA，空列表则 SoftAP，Connected 后停止 SoftAP。该演示将 Disconnected 直接转 SoftAP；迁移时需区分临时断网、重连失败和用户主动进入配网，避免网络抖动触发可见产品流程。

硬件要求包含 Flash >= 16 MB、PSRAM >= 8 MB、AudioCodecRecorder/Player 和显示触摸。圆屏上的表情/settings 需重做适配；样例直接切换 Display draw source，与 ESPocket Shell/App GUI owner 的交互需设计。Provider keys 的 menuconfig 示例只是配置入口，不能作为持久凭据治理结论。

## 可独立提取的构建工具

[analyze_build.py](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/system/super/tools/analyze_build.py) 读取 project_description、compile_commands、Ninja log/deps 和缓存配置，生成 JSON/Markdown 报告，输出只在指定 build 目录。适合先按项目目录规则评估构建耗时和 C++ 编译负担，不改变固件行为。

[compile_tuning.cmake](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/utils/brookesia_lib_utils/cmake/compile_tuning.cmake) 是被动 helper，默认 C++ pool 为 6，包含 esp-boost，可设 0 关闭；FAST_COMPILE 默认关闭，开启时减少 debug 信息。[Super CMake](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/system/super/CMakeLists.txt) 开启 ccache，并调用 [Super compile policy](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/cmake/compile_policy.cmake)。本项目可提取目标级并行限制；apply_compile_policy 依赖 System Super，不能只为 job pool 引入该 System。不能整段复制 Super CMake 或复制全局 -Wno-error=stringop-truncation 放宽 warning；构建 identity、精确 dependency/hash 检查仍须保留。是否提速需用本机 cold/warm build 证据确认。

## System Super 专项对照

沿同一固定提交进一步读取 examples/system/super 与实际 brookesia_system_super 组件，结论如下；此处仍是调查建议。

- [示例 main](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/system/super/main/main.cpp) 只负责 Services → Display → Audio binding → System init/start；40 KiB 独立启动线程与等待 10 秒均是样例选择，不能直接作为产品栈预算或健康判定。ESPocket 已有 System/Display 装配，无需复制启动入口。
- [主题与字体准备](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/system_lifecycle.cpp) 在 Shell 安装前注册字体索引、恢复主题；[font_language.hpp](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/private/font_language.hpp) 根据已注册字体的语言支持选择回退。本项目已在 App 文档加载前注册产品主题，新增价值主要是中文/多语言字体支持与回退策略。Super 的无效主题回退和本项目当前报错行为不同，是否改变需产品决策。
- [Launcher](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_app_launcher.cpp) 从 Core list_apps 过滤 manifest.visible，构建 App ID 到视图映射，安装/卸载回调刷新，环境变化更新标题与图标。适合未来 005/04 dynamic Launcher 的实现参考；不解除其 package trust/isolation 依赖，不照搬矩形网格与 Launcher Home。
- [诊断呈现](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_debug.cpp) 使用 UtilsService memory/thread 快照及警戒状态；System 使用弱 Shell 引用订阅并在 deinit 断开。可以扩展开发模式诊断，现有 MemoryProfiler checkpoint 保留；需核对锁定 Helper/Utils 接口和持续采样资源成本。
- [扩展通知](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_super/src/shell_expansion.cpp) 先订阅再读初始状态，回调只更新弱引用持有的待处理数据，Shell App timer 处理 GUI，同插槽通知合并，退出断订阅和清理 timer/dialog。板级扩展功能目前无明确需求，但该并发与清理模式可参考于网络/Assistant 状态通知，不需要新建全局通知框架。
- [资源打包](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/system/super/main/CMakeLists.txt) 收集 stage targets 并去重，LittleFS image 依赖 Runtime/Super staging。本项目已有 build tree staging，保持既有路径；对字体/新增 App 资源可核查是否补齐构建依赖。样例在 LittleFS 不可用时仅 warning，不能照搬为本项目关键资源失败策略。
- USB host/service bridge 属于 [Core lifecycle](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/system/brookesia_system_core/src/system/lifecycle.cpp) 而非示例 main 独立实现；此前总览中的 USB 项仅表示该系统装配可承载 Core 能力，不应据此引入 System Super。既有开发者模式与 USB 交互测试规则保持有效。
- [pytest_system.py](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/system/super/pytest_system.py) 只等待启动完成日志，P4 板执行；不能替代圆屏触控、App lifecycle 或资源验收。[sdkconfig.defaults](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/examples/system/super/sdkconfig.defaults) 含 TLS insecure/skip verification 和 Agent/codec 配置，不能整份导入产品。general_services 的 AFE/WakeNet 配置也不适用于当前 playback-only。

专项建议：先评估构建分析工具；产品层优先考虑字体/语言支持和开发模式诊断，动态 Launcher 等生态依赖满足后推进。Files 为独立 App 候选，Agent 集成应继续参考 Chatbot，Super manifest 中存在 Agent 依赖不等于例程完成 ESPocket Assistant 的入口与授权。

## 总体迁移建议

### 用户参考稿的补充核对

2026-10-04 用户提供一份 System Super 借鉴建议，强调产品系统与 Core 分工、Launcher 数据来源、Overlay、状态订阅和官方 App 集成。对照源码后采用其分析角度，以下仍为建议，不表示新增架构决定或实施授权：

- System Super 与 ESPocket System 都是 Core 上的产品系统。本项目 [System 类](../../../firmware/components/espocket_system/include/espocket/system.hpp) 已直接继承 Core System，Shell 是其安装/呈现对象；不能把调用链画成 System → Shell → Core。初始化、停止和 App lifecycle 应作为已实现路径的差异审计。
- Overlay 角色已存在：本项目键盘、消息弹窗和 Back 控件由 Shell 呈现，Core 持有请求关系。新增价值是 loading、重叠输入仲裁、Owner/请求身份匹配、Home/stop 清理及显示源恢复；不能从 Super 的 Overlay 名称推断存在可直接复用的通用 Overlay manager。权限决策由用户目标授权路径持有，弹窗只负责呈现与反馈。
- 状态获取也已有实现：[shell_status.cpp](../../../firmware/components/shell_circular/src/shell_status.cpp) 订阅 Wi-Fi、Battery、SNTP，并有周期刷新与退出清理。可对照 Super 改善状态到文案的映射和回调线程处理；没有第二个真实消费需求前，不预建持有重复事实的全局 Status Provider。
- 官方 Settings/Store 已接入；Files 是新增候选。Core 的包安装 API 仍需满足 005/03 的可信事务与 reboot 验证，不可把能安装/重启发现的演示认定为完整发布条件，也不应因缺口新建产品 Installer。Home/restore 仍按 Watch Face 与 Running Instance 契约判定。
- [固定提交构建规则](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/.build-rules.yml) 确有 Core/Super test_apps temporarily disabled，同时 Super example 参加构建；这只描述该构建入口覆盖范围，不能据此断言完全没有测试或组件不稳定。

因此将参考稿的广泛优先级缩为项目实际增量：loading/Overlay 行为完善、字体与语言、诊断与构建分析优先；动态 Launcher 随 package trust/isolation 前置推进；Files 单独评估。系统装配、状态与既有 App 集成先查漏，不重复建设。

建议优先研究 Chatbot 的 provider lifecycle/MCP 与本项目 Assistant 语义入口；并行可执行的候选是 HTTP 回归参考、Wi-Fi 配网和构建分析。Console 必须先限于开发模式；Recorder/AFE 在真机音频输入验证后推进。Storage 与 Super 主体以查漏为主。

项目对照基于 [Firmware README](../../../firmware/README.md)、[依赖声明](../../../firmware/main/idf_component.yml)、[System 装配](../../../firmware/components/espocket_system/src/system.cpp)与 [Card 存储](../../../firmware/components/espocket_system/src/system_cards.cpp)。当前已有 Settings/Store、Native/Runtime、导航/Card、开发模式 USB 测试及 playback-only；Agent 依赖与 Recorder/AFE 尚未进入该产品基线。迁移应保留 ADR-0006–0008 的 Owner、授权与 Running Instance 约束，以及既有 Home/PWR 产品行为。

以上是迁移建议，尚未分配新的实施任务。本次只调查源码、写研究记录并从 Spec 链接；没有修改依赖、固件或现有任务状态，也没有执行固件构建或真机验证。
