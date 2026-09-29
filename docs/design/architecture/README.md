# ESPocket 架构图集

本目录从六个互补视角描述 ESPocket。每张图只回答一个问题，避免把代码归属、运行职责、调用顺序和硬件映射挤进同一张总图。

## 阅读顺序

| 图 | 回答的问题 | 主要读者 |
|---|---|---|
| [系统上下文](01-system-context.md) | ESPocket 位于什么环境，与谁交互？ | 所有人 |
| [总体分层](02-layered-architecture.md) | 代码依赖怎样从产品层下沉到硬件？ | 架构与开发 |
| [核心模块协作](03-core-modules.md) | 运行时有哪些深模块，它们通过什么接口协作？ | 开发与测试 |
| [启动与生命周期](04-boot-lifecycle.md) | 从上电到表盘，以及 App 启停，按什么顺序发生？ | 开发与诊断 |
| [导航与应用运行](05-navigation-runtime.md) | Surface、Back、Home 和 App 生命周期如何组合？ | 产品与开发 |
| [设备能力映射](06-device-capabilities.md) | 显示、触控、电源、网络等能力怎样到达硬件？ | 平台与驱动 |

建议先读 01 和 02 建立整体心智，再按问题进入其余视图。

## 图例

- 容器表示代码所有权或运行边界；它不是新的抽象层。
- 实线箭头表示直接调用或依赖。
- 虚线箭头表示事件、回调或状态通知。
- 粗箭头表示构建、启动或生命周期主路径。
- 图中的 ESPocket、ESP-Brookesia、ESP-IDF 与硬件名称同时也是所有权标记，不额外依赖颜色区分。

## 事实边界

本图集描述当前 main 源码中的结构，并在必要处单独标出目标或受阻路径。它不代替 Milestone 验收结论：

- 当前实现以 firmware/main/app_main.cpp、firmware/components/espocket_system、firmware/components/shell_circular 和锁定的 managed components 为准。
- 产品交互目标以 [`../product/interaction-model.md`](../product/interaction-model.md) 和 [`../product/app-contract.md`](../product/app-contract.md) 为准。
- Runtime 包信任与动态安装仍以 [`../policies/package-trust.md`](../policies/package-trust.md) 的门槛为准。
- 是否通过真机验收只由 ../../milestones/ 中的报告判定。

## 维护规则

1. 源码中的依赖、生命周期或设备路径改变时，只更新对应视图。
2. 不在总图中展开上游框架的全部内部实现；调用者只需要理解其公开接口和关键行为。
3. 第二个真实 Adapter 出现前，不把假设中的扩展点画成既有 seam。
4. 图中保留真实类名、manifest ID 与模块名，说明文字使用中文。
5. 修改 `tools/generate-diagrams.mjs` 后运行 `node docs/design/architecture/tools/generate-diagrams.mjs`，重新生成全部 SVG。
6. 提交前运行 `node docs/design/architecture/tools/check-diagram-layout.mjs`，检查文字和连线碰撞；该脚本需要可用的 Chrome/Chromium，也可通过 `CHROME_PATH` 指定。
