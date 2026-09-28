# Design Documents

本目录描述跨 Milestone 保持有效的产品、架构和交互约束。

| 文档 | 职责 |
|---|---|
| [项目设计](project.md) | 产品定位、架构边界、阶段门与依赖策略 |
| [交互设计](interaction.md) | Home、Launcher、Quick Settings、App 导航与圆屏规则 |
| [Package Trust Gate](package-trust.md) | Runtime 包验证、安装、重启发现与回滚契约 |
| [Launcher Synchronization](launcher-sync.md) | 固定入口与可信动态入口的同步策略 |

设计文档可以定义尚未实现的目标状态，但必须明确区分“目标规范”和“当前行为”。实现结果与验收状态只在 [`../milestones/`](../milestones/README.md) 中判定。
