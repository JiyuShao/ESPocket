# 设计文档

本目录描述跨 Milestone 保持有效的产品、架构、交互和产品策略。阶段状态与验收结果不在此维护。

| 分组 | 文档 | 职责 |
|---|---|---|
| 产品 | [产品总览](product/overview.md) | 产品定位、长期约束、架构边界与依赖策略 |
| 产品 | [系统交互模型](product/interaction-model.md) | Home、Launcher、Quick Settings、App 导航与圆屏规则 |
| 产品 | [App 交互契约](product/app-contract.md) | Native、Runtime 与第三方 App 的 Root/Detail/Back、生命周期和页面指导 |
| 架构 | [架构图集](architecture/README.md) | 系统上下文、分层、核心模块、生命周期、导航与设备能力视图 |
| 策略 | [包信任门](policies/package-trust.md) | Runtime 包验证、安装、重启发现与回滚契约 |
| 策略 | [Launcher 同步策略](policies/launcher-sync.md) | 固定入口与可信动态入口的同步策略 |

设计文档可以定义尚未实现的目标状态，但必须明确区分“目标规范”和“当前行为”。实现结果与验收状态只在 [`../milestones/`](../milestones/README.md) 中判定。

## 目录职责

```text
design/
├── product/        # 长期产品约束与交互契约
├── architecture/   # 当前源码架构视图、SVG 与生成工具
└── policies/       # 尚需执行或解锁的产品策略
```
