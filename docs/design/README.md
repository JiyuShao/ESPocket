# 设计文档

本目录只保存跨 Milestone 持续有效的产品契约和架构视图。选择理由见 [ADR](../adr/README.md)，实施计划见根目录 `.scratch/`，阶段结论见 [Milestones](../milestones/README.md)。

## 产品

- [产品总览](product/overview.md)
- [系统交互模型](product/interaction-model.md)
- [App 交互契约](product/app-contract.md)
- [Runtime 包信任契约](product/runtime-package-trust.md)
- [App 发现与 Launcher 契约](product/application-discovery.md)

## 架构

- [架构视图入口](architecture/README.md)
- [AI Native 跨模块视图](architecture/07-ai-native.md)

产品文档回答“必须表现成什么”；架构文档回答“Owner、依赖和生命周期如何组合”。两者都不维护阶段状态表。
