# ESPocket 文档

每类信息只有一个权威位置。先按问题选择入口，不从 README 复制具体状态或设计细节。

| 想知道什么 | 权威位置 |
|---|---|
| 项目术语是什么 | [`CONTEXT.md`](../CONTEXT.md) |
| 为什么作出难以逆转的选择 | [ADR](adr/README.md) |
| 产品必须怎样表现 | [产品设计](design/product/overview.md) |
| 当前或目标结构怎样组织 | [架构视图](design/architecture/README.md) |
| 当前要做什么、如何拆票 | [`.scratch/`](../.scratch/) |
| 阶段是否通过、证据在哪里 | [Milestones](milestones/README.md) |
| 某个上游版本实际提供什么 | [Upstream Tracking](upstream/README.md) |
| 如何构建或执行验收 | [Guides](guides/README.md) |
| Agent 如何读取这些文档 | [Agent docs](agents/domain.md) |

## 路由规则

- 长期产品行为进入 `design/product/`。
- 当前结构和跨模块关系进入 `design/architecture/`。
- 选择理由进入 `adr/`。
- 当前改动方案进入 `.scratch/<effort>/spec.md`。
- 可独立执行的工作进入 `.scratch/<effort>/issues/`。
- 阶段门槛、判定和证据索引进入 `milestones/`。
- 特定上游版本事实进入 `upstream/`。
- 人工操作步骤进入 `guides/`。

同一含义只在一个位置完整定义，其他文档通过链接引用。设计文档可以描述目标状态，但不能把未通过的 Milestone 写成当前事实。

## 验证

修改文档后运行：

```bash
python3 scripts/check-docs.py
```

原始证据一旦被 acceptance 引用便保持不可变；新增观察使用新文件。
