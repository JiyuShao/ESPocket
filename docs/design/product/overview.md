# ESPocket 产品总览

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
- Pet、XiaoZhi、AI UI、MCP 与 ESP-Claw 不属于当前产品基线；应在平台与基础交互契约验证完成以后单独规划。

## 架构边界

```text
app_main
   ↓
espocket::System
   ├── installs → HelloApp
   ├── scans staged package → Hello Runtime
   ├── installs → official SettingsApp
   ├── installs → official AppStoreApp
   └── installs/starts → CircularShell
```

`espocket::System` 继承 Brookesia System Core，负责产品装配、系统生命周期、GUI backend、Shell App 的安装与启动，以及 PWR 输入和显示状态编排。圆屏布局、Watch Face、Launcher、状态呈现和触摸手势属于 `shell_circular`。

Circular Shell 使用隐藏 Native `IApp` 作为 Brookesia 承载机制，但它是系统 Shell，不出现在普通应用列表中。完整运行关系见[架构图集](../architecture/README.md)。

允许依赖：

```text
espocket_system → shell_circular
espocket_system → app_hello
espocket_system → Brookesia System Core
Applications    → Brookesia App interfaces
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
- 目标交互契约见[系统交互模型](interaction-model.md)与 [App 交互契约](app-contract.md)。

## 错误分类

Fatal：Display、Touch、System Core、Shell 基础启动。Fatal 失败必须记录错误并停止启动，保留串口诊断；不自动重启，不实现错误 UI。

Recoverable：Time、Wi-Fi status、Battery status。数据不可用时分别显示 `--:--` 或 `unknown`，不得阻塞 Shell 启动。

## 依赖与版本策略

- 正式依赖通过 ESP Component Registry 声明。
- `managed_components/` 与 `build/` 不提交，`dependencies.lock` 提交。
- 上游源码 checkout 只作 reference，不作为 vendor dependency。
- 不修改 `managed_components/`。
- interface、Kconfig、manifest 和类名必须以锁定版本官方源码为准，禁止根据模型记忆猜测。
- 第一次成功构建后，将 ESP-IDF、解析后的 Brookesia 模块和 `dependencies.lock` 作为一个 Platform Baseline。
- 框架升级必须独立进行并重新执行完整 Smoke Test。

Runtime 包信任和动态 Launcher 的目标策略分别见[包信任门](../policies/package-trust.md)与 [Launcher 同步策略](../policies/launcher-sync.md)。阶段状态、范围和验收证据统一由 [Milestone 总览](../../milestones/README.md)维护。

## 长期原则

1. ESPocket 不等同于 Circular Shell。
2. ESPocket 不是 ESP-Brookesia Fork。
3. V0.x 只做好 Waveshare 1.75C。
4. 第二个真实实现出现以后再抽象。
5. 先验证平台，再开发 Pet 和 AI。
