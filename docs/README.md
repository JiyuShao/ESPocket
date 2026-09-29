# ESPocket 文档

本目录是 ESPocket 的设计、阶段验收和上游协作入口。项目当前状态以本页和各 Milestone 验收文档为准；原始串口、构建与诊断记录只作为证据，不承担设计说明职责。

## 快速入口

- [设计文档](design/README.md)：产品约束、架构、交互契约与产品策略。
- [架构图集](design/architecture/README.md)：系统上下文、分层、模块协作、生命周期、导航和设备能力。
- [系统交互模型](design/product/interaction-model.md)：Home、Launcher、Quick Settings、App 导航与圆屏交互约束。
- [Milestone 总览](milestones/README.md)：M1–M8 状态、验收文档与下一解锁条件。
- [上游状态](upstream/README.md)：Brookesia 阻塞项、核查记录与待提交 Issue。

## 目录职责

```text
docs/
├── README.md                 # 文档入口与维护规则
├── design/                   # 产品、架构、交互契约和产品策略
├── milestones/               # 阶段规范、验收结果和原始证据
│   └── evidence/             # 按阶段归档的不可变记录
└── upstream/                 # 上游版本核查、Issue 草稿与附件
```

## 当前状态

| Milestone | 状态 | 摘要 |
|---|---|---|
| M0 | `WAIVED` | 官方基线由项目所有者明确豁免 |
| M1 | `PASS` | System 与 Circular Shell 基线 |
| M2 | `PASS` | Native App 生命周期与 50-cycle heap gate |
| M3 | `PASS` | Runtime 集成与生命周期已验收；独立 `.bpk` file-install 门槛由项目所有者接受 |
| M4 | `BLOCKED` | 部分设备能力未验收；Audio 受上游边界阻塞 |
| M5 | `BLOCKED` | HTTP cancel race、package trust 与兼容发布路径 |
| M6 | `IN PROGRESS` | Watch Face、PWR 与显示状态主机侧实现完成；真机验收未执行 |
| M7–M8 | `NOT ENTERED` | 源码已提前开发并通过主机侧门槛；按依赖顺序等待真机验收 |

详细判定和证据入口见 [Milestone 总览](milestones/README.md)。

真机返回后的执行顺序与记录模板见 [真机验收执行清单](milestones/hardware-acceptance-runbook.md)。

## 维护规则

1. 设计文档描述长期边界，不复制完整验收日志。
2. 每个 Milestone 只有一个验收文档；状态只能使用文档中定义的判定。
3. 原始证据一旦被验收文档引用，不原地改写；需要修订时新增文件并记录替代关系。
4. 上游问题材料与产品验收分开归档；上游修复不能自动等同于本项目验收通过。
5. README 只提供导航和摘要，具体事实以链接到的源文档为准。
