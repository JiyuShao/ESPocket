# ESPocket 文档

每类信息只有一个权威位置。先按问题选择入口，不从 README 复制具体状态或设计细节。

| 想知道什么 | 权威位置 |
|---|---|
| 项目术语是什么 | [`CONTEXT.md`](../CONTEXT.md) |
| 为什么作出难以逆转的选择 | [ADR](adr/README.md) |
| 产品必须怎样表现 | [产品设计](design/product/README.md) |
| 当前或目标结构怎样组织 | [架构视图](design/architecture/README.md) |
| 当前要做什么、如何拆票 | [`.scratch/`](../.scratch/) |
| App 开发 API 与测试协议 | [开发契约](development/README.md) |
| 阶段是否通过、门槛与证据索引在哪里 | [Milestones](milestones/README.md) |
| 某个上游版本实际提供什么 | [Upstream Tracking](upstream/README.md) |
| 如何构建 firmware | [Firmware README](../firmware/README.md) |
| Agent 如何读取这些文档 | [Agent docs](agents/domain.md) |

## 路由规则

- 长期产品行为进入 `design/product/`。
- 当前结构和跨模块关系进入 `design/architecture/`。
- 选择理由进入 `adr/`。
- 当前改动方案进入 `.scratch/<effort>/spec.md`。
- 可独立执行的工作进入 `.scratch/<effort>/issues/`。
- 阶段门槛、判定、验收步骤和证据索引进入 `milestones/`。
- 特定上游版本事实进入 `upstream/`。
- 与 firmware 直接相关的长期操作说明进入 `firmware/README.md`。

同一含义只在一个位置完整定义，其他文档通过链接引用。设计文档可以描述目标状态，但不能把未通过的 Milestone 写成当前事实。

产品契约与架构视图的职责边界见[设计文档索引](design/README.md)。

## 验证

修改文档后运行：

```bash
python3 scripts/docs/check.py
```

[Documentation workflow](../.github/workflows/docs.yml) 在相关 pull request 与 push 中执行同一命令。

阶段 acceptance 与 records 保存日期、镜像 identity、关键测量值、失败和未验证项。原始构建或串口日志只作为本地、CI 或 Release artifact 临时保存，不进入源码树。
