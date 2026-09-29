# ESPocket 架构

这些视图描述当前源码结构和已经决定的目标关系。目标关系会明确标注，是否实现与验收仍由 Spec、ticket 和 Milestone 判定。

| View | Question |
|---|---|
| [01 系统上下文](01-system-context.md) | ESPocket 与用户、构建、网络和诊断环境如何相交？ |
| [02 总体分层](02-layered-architecture.md) | 产品、框架、Adapter 和硬件怎样单向依赖？ |
| [03 核心模块](03-core-modules.md) | 深模块分别拥有什么，如何协作？ |
| [04 启动与生命周期](04-boot-lifecycle.md) | 系统和 App 怎样启动、停止与失效？ |
| [05 导航与应用运行](05-navigation-runtime.md) | Surface、App、Back、Home 和 Display State 怎样组合？ |
| [06 设备能力](06-device-capabilities.md) | 产品能力如何到达 Service、Adapter 和硬件？ |
| [07 AI Native](07-ai-native.md) | 语义访问怎样注册到真实 Owner 并保持授权与生命周期？ |

AI Native 不单独重定义产品词汇或列出实施工作。词义在根目录 `CONTEXT.md`，产品行为分布在产品契约，具体工作在 `.scratch/009-ai-native-foundation/`。

## 图例与维护

- 容器表示所有权或运行边界。
- 实线表示调用或依赖，虚线表示事件，粗线表示主路径。
- 第二个真实 Adapter 出现前，不把假设扩展点画成既有 seam。
- 当前源码图保留真实模块名；目标关系明确写出“目标”或 Exposure Decision。

重新生成并检查图：

```bash
node docs/design/architecture/tools/generate-diagrams.mjs
python3 scripts/check-docs.py
```
