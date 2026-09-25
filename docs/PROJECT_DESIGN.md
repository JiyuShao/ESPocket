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
   │ owns
   ↓
CircularShell
```

`espocket::System` 基于 Brookesia System Core，负责产品装配、系统生命周期、GUI backend、隐藏 Shell App 的安装与启动。圆屏布局、Launcher、状态呈现和 Home 手势只属于 `shell_circular`。

Circular Shell 使用隐藏 Native `IApp` 作为 Brookesia 承载机制，但它是系统 Shell，不出现在普通应用列表中。M1 不把这种承载机制描述为通用 App 生命周期验证。

允许依赖：

```text
espocket_system → shell_circular
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
M1 ESPocket System         — 当前阶段
M2 Native App Validation
M3 Runtime App Validation
M4 Device Capabilities
M5 Application Ecosystem
M6 Product Experience
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

M1 通过条件包括真实设备显示、触摸、状态降级、Home 手势，以及 10 次冷启动和 10 次 EN/软件重启。未执行项只能标记 `NOT TESTED`；外部条件阻塞项标记 `BLOCKED`。

每个 Milestone 完成后必须输出验收报告并停止；未经项目所有者明确批准不得进入下一阶段。M1 真机验收通过前不发布 Release、不创建 `v0.1-system`。

## 依赖与版本策略

- 正式依赖通过 ESP Component Registry 声明。
- `managed_components/` 与 `build/` 不提交，`dependencies.lock` 提交。
- 上游源码 checkout 只作 reference，不作为 vendor dependency。
- 不修改 `managed_components/`。
- API、Kconfig、manifest 和类名必须以锁定版本官方源码为准，禁止根据模型记忆猜测。
- 第一次成功构建后，将 ESP-IDF、解析后的 Brookesia 组件和 `dependencies.lock` 作为一个 Platform Baseline。
- 框架升级必须独立进行并重新执行完整 Smoke Test。

## 后续 Milestone

- M2：`app_hello` 验证 Native App 生命周期与 50 次启停稳定性。
- M3：只启用 JavaScript Runtime，以官方 `.bpk` 验证 Runtime App 与 Native App 共存。
- M4：Settings、Wi-Fi 配置、亮度、音量、时间、存储、电池、设备信息和 Developer Mode。
- M5：复用官方 App Store，验证 Runtime App 下载、安装、更新和卸载。
- M6：平台成立以后才开发 Pet、XiaoZhi 与后续产品体验。

## 长期原则

1. ESPocket 不等同于 Circular Shell。
2. ESPocket 不是 ESP-Brookesia Fork。
3. V0.x 只做好 Waveshare 1.75C。
4. 第二个真实实现出现以后再抽象。
5. 先验证平台，再开发 Pet 和 AI。
