# ESPocket 产品设计

本目录定义 ESPocket 必须向用户呈现的长期产品行为。文档按编号顺序阅读；每条可验证要求都有稳定 ID，供设计、实现和验收引用。

1. [产品总览](01-overview.md)
2. [AI Native](02-ai-native.md)
3. [系统交互模型](03-interaction-model.md)
4. [App 契约](04-app-contract.md)
5. [Runtime 包信任](05-runtime-package-trust.md)
6. [App 发现与 Launcher](06-application-discovery.md)
7. [开发者模式与交互验证](07-developer-mode-testing.md)

8. [系统能力对齐](08-system-capability-alignment.md)

“必须”表示产品不可违反的要求，“应该”表示除非有明确理由否则遵守的默认规则，“可以”表示可选能力。产品规则发生变化时，不得用既有 Requirement ID 表达另一项含义；替代关系必须显式记录。

这里不记录实施状态、选择过程、任务拆分、源码位置或验收材料。
