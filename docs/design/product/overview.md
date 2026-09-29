# ESPocket 产品总览

> 文档类型：长期产品设计。阶段状态和实现证据只由 [Milestone 总览](../../milestones/README.md)判定。

## 定位

ESPocket 是基于 ESP-Brookesia、面向 ESP 系列轻量智能设备的应用平台。ESPocket 负责产品语义、装配和交互契约；ESP-Brookesia 提供 App、Runtime、Service、GUI 与设备框架。

```text
Applications
    ↓
ESPocket product contracts
    ↓
ESP-Brookesia public seams
    ↓
ESP-IDF and hardware
```

ESPocket 不是宠物 App、XiaoZhi 固件、圆屏 Launcher、Waveshare Demo、ESP-Brookesia Fork 或 System Super 换皮。

## 产品边界

- ESPocket System 是产品装配和跨模块策略边界。
- Shell 是系统交互环境；Circular Shell 是首个实现，不代表整个平台。
- Native App 与 Runtime App 是两种执行模型，共用产品交互和生命周期契约。
- 官方 System App 通过明确的产品装配进入系统，不形成第三种执行模型。
- App、Service 和 Runtime 不依赖 Circular Shell 内部实现。
- 产品通过 Brookesia 公开 seam 使用框架能力，不复制框架 Manager、Package Format、HAL 或 Store backend。

上述边界的理由见 [ADR-0001](../../adr/0001-espocket-is-a-product-layer-over-brookesia.md) 和 [ADR-0003](../../adr/0003-native-and-runtime-share-the-system-core-contract.md)。

## V0.x 产品范围

- 唯一目标硬件是 Waveshare ESP32-S3-Touch-AMOLED-1.75C。
- Board Manager selector 是 `esp32_s3_touch_amoled_1_75c`。
- 产品实现可以针对 466×466 圆形 AMOLED 优化，但 ESPocket 的定义不绑定圆屏。
- V0.x 只实现 Circular Shell；第二个真实 Shell 出现前不创建通用 Shell Factory、Manager、Registry 或 Plugin。
- Pet、XiaoZhi、MCP 和 ESP-Claw 需要独立产品设计，不能凭底层接口存在而进入基线。

## 交互方向

- Watch Face 是唯一 Home 和 Home Space 的中心。
- Launcher 只负责发现和启动 App。
- Home、Back 与 Display State 是不同语义。
- App 只记录一个直接 Launch Source，不维护任意跨 App 历史链。
- Native 与 Runtime App 使用同一 Root、Detail、Back、Home、恢复和回收契约。
- 圆屏主要内容位于中部，系统手势不占用 App 的普通滚动与横滑。

完整规则见[系统交互模型](interaction-model.md)和 [App 交互契约](app-contract.md)。

## AI Native

AI Native 是 ESPocket 的基础产品与架构设计维度，而不是后加的功能层。每项新系统设计都必须给出 Exposure Decision：注册稳定产品语义、明确不暴露，或延后并建立 ticket。

语义注册必须位于真实 Owner 边界，并同时定义 Context、Action、Event、授权、Action Risk 和生命周期。内部实现、HAL 方法与框架对象不因“可调用”而自动成为 AI 能力。

这项要求不强制每个内部模块暴露能力；它强制每项产品能力在设计时完成判断。具体决定见 [ADR-0006](../../adr/0006-ai-semantic-access-stays-with-real-owners.md) 至 [ADR-0009](../../adr/0009-ai-native-is-a-foundational-design-dimension.md)，系统关系见 [AI Native 架构](../architecture/07-ai-native.md)。

## 应用生态

- 远程 Runtime 包只有通过 Core-owned 信任门后才能安装、重启发现和进入 Launcher。
- Launcher 的动态部分只投影 Core 已提交的 App 状态。
- 固定产品入口与动态 App 分开管理；动态路径不可用时固定入口保持可用。

长期契约见 [Runtime 包信任](runtime-package-trust.md)和 [App 发现与 Launcher](application-discovery.md)。

## 产品韧性

- Display、Touch、System Core 与 Shell 基础启动失败属于 Fatal，必须停止启动并保留诊断。
- Time、Wi-Fi 与 Battery 状态不可用属于 Recoverable，产品使用明确降级状态继续启动。
- Screen Off 不改变导航；恢复目标失效时回 Watch Face。
- App 不得依赖后台驻留，长期能力由 Service 或持久化业务状态承担。

## UI 原则

- 默认通过 Brookesia JSON UI、GUI Interface 和 LVGL backend 实现界面。
- JSON UI 不适合的局部能力可以使用 Native LVGL。
- Circular Shell 可以拥有圆屏安全区和校准参数；ESPocket System 不包含设备 UI 布局。
- 第二个真实实现出现后再提取通用抽象。
