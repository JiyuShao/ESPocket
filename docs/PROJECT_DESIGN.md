# ESPocket 项目设计

## 定位

ESPocket 是一个基于 ESP-Brookesia、面向 ESP 系列轻量智能设备的应用平台。ESPocket 负责产品平台层；ESP-Brookesia 负责基础应用框架层。

```text
Applications
    ↓
ESPocket
    ↓
ESP-Brookesia
    ↓
ESP-IDF
    ↓
Hardware
```

ESPocket 不是宠物 App、XiaoZhi 固件、圆屏 Launcher、Waveshare 专用 Demo、ESP-Brookesia Fork 或 System Super 换皮。

## V0.x 产品约束

- 唯一目标硬件：Waveshare ESP32-S3-Touch-AMOLED-1.75C。
- 官方 Board Manager selector：`esp32_s3_touch_amoled_1_75c`。
- 架构不把 ESPocket 定义为圆屏系统；产品实现可以完全针对 466×466 圆形 AMOLED 优化。
- V0.x 只实现 Circular Shell。
- 没有第二个真实 Shell 前，不创建 `IShell`、Factory、Manager、Registry 或 Plugin。
- Pet、XiaoZhi、AI UI、MCP 与 ESP-Claw 全部推迟到平台验证完成以后。

## 架构边界

```text
app_main
   ↓
espocket::System
   ├── installs → HelloApp
   ├── scans staged package → Hello Runtime
   ├── installs → official SettingsApp
   ├── installs → official AppStoreApp
   └── owns/starts → CircularShell
```

`espocket::System` 基于 Brookesia System Core，负责产品装配、系统生命周期、GUI backend、隐藏 Shell App 的安装与启动。圆屏布局、Launcher、状态呈现和 Home 手势只属于 `shell_circular`。

Circular Shell 使用隐藏 Native `IApp` 作为 Brookesia 承载机制，但它是系统 Shell，不出现在普通应用列表中。M1 不把这种承载机制描述为通用 App 生命周期验证。

允许依赖：

```text
espocket_system → shell_circular
espocket_system → app_hello
espocket_system → Brookesia System Core
Applications    → Brookesia App APIs
```

禁止依赖：

```text
App / Service / Runtime App → CircularShell internals
Domain                       → Brookesia / LVGL
Service                      → Launcher implementation
```

ESPocket 不重新实现 App Manager、Runtime Manager、GUI Manager、Timer Manager、Package Manager、HAL、Package Format 或 App Store backend。

## UI 原则

- ESPocket 默认采用 Brookesia JSON UI + GUI Interface + LVGL backend。
- 只有 JSON UI 明显不适合时才局部使用 Native LVGL。
- 不为未来需求预建空资源目录、主题、模板或 Flow。
- Circular Shell 可包含 466×466、圆屏安全区和真机校准参数；`espocket_system` 不包含这些设备 UI 细节。

## 错误分类

Fatal：Display、Touch、System Core、Shell 基础启动。Fatal 失败必须记录错误并停止启动，保留串口诊断；不自动重启，不实现错误 UI。

Recoverable：Time、Wi-Fi status、Battery status。数据不可用时分别显示 `--:--` 或 `unknown`，不得阻塞 Shell 启动。

## 阶段门

```text
M0 Official Baseline       — WAIVED
M1 ESPocket System         — PASS（v0.1-system）
M2 Native App Validation   — PASS（2026-09-26）
M3 Runtime App Validation  — BLOCKED（Core .bpk file-install only）
M4 Device Capabilities     — BLOCKED（keyboard physical proof + audio + remaining controls）
M5 Application Ecosystem   — BLOCKED（remote/trust/runtime-isolation/catalog/sync gates）
M6 Product Experience      — NOT ENTERED
```

### M0 决策

- Status: `WAIVED`
- Date: 2026-09-25
- Decision: 项目所有者选择直接进入 M1。
- Consequence: 官方基线风险被接受，并在 M1 中暴露和处理；M0 不得标记为 PASS。

### M1 范围

```text
espocket::System
   └── CircularShell
       ├── Launcher
       │   └── Shell Preview → TestPage
       └── ShellOverlay
           ├── StatusView
           │   ├── Clock
           │   ├── Wi-Fi
           │   └── Battery
           ├── HomeIndicator
           └── HomeGesture
```

唯一需要证明的用户行为：

```text
Boot → Launcher → tap → TestPage → bottom swipe → Launcher
```

M1 不包含 Native App 注册/发现/启动/停止验证、资源清理、Runtime、Recents、Notifications、Quick Settings、独立 Home 页面或通用手势框架。`TestPage` 在 M2 引入 `Hello Native` 后删除。

M1 通过条件包括真实设备显示、触摸、状态降级、Home 手势，以及 5 次冷启动和 10 次 EN/软件重启。未执行项只能标记 `NOT TESTED`；外部条件阻塞项标记 `BLOCKED`。

### M2 范围

```text
espocket::System
   ├── direct install → HelloApp（visible Native IApp）
   └── direct install/start → CircularShell（hidden Native IApp）
                                  ├── Launcher → Hello Native
                                  └── SystemTop Overlay → Home Gesture
```

M2 保持 `install_registered_apps = false`，由产品装配层显式安装唯一的 `HelloApp`；不为一个实现增加 Provider、Registry 或 App Manager。Launcher 按稳定 manifest ID 通过 Core `SystemApi` 启动 App。System lifecycle hook 为每次可见 foreground run 发布单调 generation token。Display Home callback 在 `Press` 时快照 token，首次越阈值后只发布一次 intent，不读取 Core app map 或调用 Core；Shell-owned timer 在 Core app task 内消费 intent，并在 generation、tracked AppId 与 Core active app 一致时同步 `stop_app()`。这使一次物理手势绑定到触摸开始时的运行代次，不能误停同 AppId 的新 run。stop 或 start/stop failure 后由 ESPocket System hook 统一重新挂载 Launcher。Hello 只使用 Core-owned 的无 handler action subscription 和 GUI document，不建立自己的 timer、task 或连接管理。

M2 的 50-cycle 验收由默认关闭的 `CONFIG_ESPOCKET_M2_LIFECYCLE_STRESS` 驱动真实 `start_app()` / `stop_app()`。每轮检查 `Running`、`Stopped`，并通过公开 GUI API 的负向探针证明 `preload_dom=false` 的 Hello document 已卸载后记录 `gui=Unloaded`；随后使用 Brookesia allocation-free raw heap snapshot 记录 internal/PSRAM free 与 largest block。Host 工具只读取串口并验证唯一的一次运行，拒绝拼接的 reboot attempt 及 Core GUI cleanup warnings，不远程控制生命周期。

M2 通过条件包括 Launcher → Hello → Increment → Home → Launcher 的真机交互，以及 50/50 生命周期循环。cycle 1 为 warm-up；cycles 2–6 与 46–50 的四项停止态内存中位数损失均不得超过 1 KiB，cycles 2–50 不得出现任一指标跨 5 个连续样本严格下降，也不得出现 panic、watchdog、assert 或 heap corruption。

每个 Milestone 必须输出独立验收报告；未执行项只能标记 `NOT TESTED`，外部条件阻塞项标记 `BLOCKED`。项目所有者于 2026-09-26 授权连续实施到 M5，非重大人工检查可集中延期，但缺少规定证据的 Milestone 不得标记 `PASS`。该授权不包含烧录、Git commit/push/tag、Release 或进入 M6。

### M3 范围

M3 只启用官方 JavaScript Runtime。`Hello Runtime` 使用 stable package ID `espocket.app.hello_runtime`，与 Native Hello 同时显示在固定 Launcher 中。System Core 的官方 staging helper 将 unpacked 源包预置到 `/littlefs/apps/<package-id>`，Core 在 boot 时扫描 package app；该路径只验证预置发现/加载，不等于 `.bpk` install。

官方 `.bpk` 由 `esp-brookesia-toolkit@1.0.1` 构建，Runtime backend 使用 `espressif/brookesia_runtime_js@0.8.3`。项目所有者已逐项授权相关外部源码执行；ESP-IDF Component Manager 已将 Runtime JS 0.8.3 与确切的 QuickJS-NG 0.14.0 解析写入 lock，且 clean 固件构建/启动、链接保留、unpacked staging、LittleFS image、Runtime render/Home 与 Native/Runtime 双向交替均已通过。Toolkit npm lock、doctor、debug build、`.bpk` 结构与内容已验证；Core `.bpk` file-install 与 release signing 尚未执行。

## 依赖与版本策略

- 正式依赖通过 ESP Component Registry 声明。
- `managed_components/` 与 `build/` 不提交，`dependencies.lock` 提交。
- 上游源码 checkout 只作 reference，不作为 vendor dependency。
- 不修改 `managed_components/`。
- API、Kconfig、manifest 和类名必须以锁定版本官方源码为准，禁止根据模型记忆猜测。
- 第一次成功构建后，将 ESP-IDF、解析后的 Brookesia 组件和 `dependencies.lock` 作为一个 Platform Baseline。
- 框架升级必须独立进行并重新执行完整 Smoke Test。

## 后续 Milestone

- M2：`app_hello`、真机交互与 50 次启停/heap gate 已于 2026-09-26 通过。
- M3：JavaScript Runtime dependency、clean 固件、unpacked staging、LittleFS、Toolkit debug `.bpk`、Runtime render/Home 与 Native/Runtime 交替已验证；仍缺 Core `.bpk` file-install 与 release signing。
- M4：官方 Settings clean lifecycle、466×466 smoke、Wi-Fi 页面、Brightness、Time、Device Info 与 Home 已验证；系统键盘和 Wi-Fi 10/10 候选已 app-only 写入并通过 90 秒启动验证，Wi-Fi 初始化、保留 NVS 下的联网与 SNTP 同步均有脱敏真机证据；键盘 provider 已有一次真机 open/close，但掩码、模式、输入、确认/取消与清理语义以及 Storage/Battery/Developer 仍未单独确认，Sound 受 HAL Adaptor playback-only Kconfig/manifest 缺陷阻塞。
- M5：官方 App Store clean offline lifecycle 与 Home 已验证；先前在线真机已成功拉取并缓存远程索引与部分 HTTPS 元数据，但并发请求/取消阶段出现一次 `LoadProhibited`、两次 `StoreProhibited` 与三次自动重启。`-0x008D` 已确认为内部 RAM TLS 分配失败；官方 HTTP Kconfig 1 worker / 1 concurrent request 的产品 containment 已完成 host build、app-only 写入、90 秒无 fatal 启动与缓存态 Store/Home 验证。后续显式 Refresh 成功提交远程索引/图标请求并写入 index cache，且未再出现 `-0x008D`；但 index 连接超时/重试后的 Store refresh timeout 紧接触发 `LoadProhibited`（`EXCVADDR=0x8`）与自动重启，符号化崩溃栈位于 HTTP worker 的 Mbed TLS handshake。该 containment 只缓解已观测的 TLS 分配压力，不是在线稳定性或上游竞态修复。package digest/signature 未强制执行，Core `KeyboardClosed.Text` 缺少 owner isolation（产品仅在 Runtime stop failure 后 fail-closed），已知官方包仅支持 `super`，兼容发布路径与 Launcher sync 仍阻塞。
- M6：平台成立以后才开发 Pet、XiaoZhi 与后续产品体验。

## 长期原则

1. ESPocket 不等同于 Circular Shell。
2. ESPocket 不是 ESP-Brookesia Fork。
3. V0.x 只做好 Waveshare 1.75C。
4. 第二个真实实现出现以后再抽象。
5. 先验证平台，再开发 Pet 和 AI。
