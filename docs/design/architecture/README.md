# ESPocket 架构

本目录描述已经决定的目标结构：Module 如何分工、Interface 位于什么 Seam、Adapter 如何连接框架与硬件，以及生命周期由谁拥有。实现进度、阻塞、日期和验收结论不属于架构文档。

| View | Question |
|---|---|
| [01 — 系统上下文](01-system-context.md) | ESPocket 与用户、构建、网络和诊断环境如何相交？ |
| [02 — 总体分层](02-layered-architecture.md) | 产品、框架、Adapter 和硬件怎样单向依赖？ |
| [03 — 核心 Module](03-core-modules.md) | 深 Module 分别拥有什么，如何通过小 Interface 协作？ |
| [04 — 启动与生命周期](04-boot-lifecycle.md) | 系统和 App 怎样启动、停止与失效？ |
| [05 — 导航与应用运行](05-navigation-runtime.md) | Surface、App、Back、Home 和 Display State 怎样组合？ |
| [06 — 设备能力](06-device-capabilities.md) | 产品能力如何到达 Framework Interface、Adapter 和硬件？ |
| [07 — AI Native](07-ai-native.md) | 语义访问怎样注册到真实 Owner，并维持授权与生命周期？ |

## 维护规则

- 每篇架构文档必须列出所支撑的 Product Requirement ID。
- 架构不变量使用稳定 ID；修改含义时新增或明确替代，不复用旧 ID。
- 每个系统设计必须包含 AI Native Exposure Decision。
- Code Anchors 只指向架构的实际接入点，不承担状态说明。
- 第二个真实 Adapter 出现前，不建立假设性的 Factory、Registry 或扩展 Interface。

重新生成并检查图：

```bash
node scripts/docs/generate-architecture-diagrams.mjs
python3 scripts/docs/check.py
```
