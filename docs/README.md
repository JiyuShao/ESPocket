# ESPocket 文档

每类信息只有一个权威位置。

| 想知道什么 | 权威位置 |
|---|---|
| 项目术语是什么 | [CONTEXT.md](../CONTEXT.md) |
| 为什么作出难以逆转的选择 | [ADR](adr/README.md) |
| 产品必须怎样表现 | [产品设计](design/product/README.md) |
| 当前或目标结构怎样组织 | [架构视图](design/architecture/README.md) |
| 当前任务、依赖、状态和验收结果是什么 | [.scratch](../.scratch/README.md) |
| App 开发 API 与测试协议 | [开发契约](development/README.md) |
| 某个上游版本实际提供什么 | [Upstream Tracking](upstream/README.md) |
| 如何构建 firmware | [Firmware README](../firmware/README.md) |
| Agent 如何读取这些文档 | [Agent docs](agents/domain.md) |

## 路由规则

- 长期产品行为进入 `design/product/`。
- 当前结构和跨模块关系进入 `design/architecture/`。
- 选择理由进入 `adr/`。
- 工作范围、整体状态和结果摘要进入 `.scratch/<effort>/spec.md`。
- 可执行工作、具体依赖、验收条件、步骤和完成结果进入 `.scratch/<effort>/issues/`。
- 日期、镜像 identity、测量值、失败、豁免与未验证项进入对应 Effort 的 `records/`，由 Spec 或 ticket 链接。
- 特定上游版本事实进入 `upstream/`。
- 与 firmware 直接相关的长期操作说明进入 `firmware/README.md`。

Spec/ticket 是工作状态的权威；records 保存有日期的历史事实。代码完成、构建通过与真机通过分别记录。设计文档可以描述目标，但只有对应证据成立后才能写成已实现。

产品契约与架构视图的职责边界见[设计文档索引](design/README.md)。

## 验证

修改文档后运行：

```bash
python3 scripts/docs/check.py --markdown
```

`--markdown` 检查 Markdown 结构、链接和文档规则，不启动 Chrome；不传参数时也执行这一检查。修改架构 SVG、图生成器或图布局检查器后，另运行：

```bash
python3 scripts/docs/check.py --diagrams
```

图检查需要 Node.js 与 Chrome／Chromium。[Host-check workflow](../.github/workflows/host-check.yml) 在相关 pull request 与 push 中运行 `python3 scripts/check.py --diagrams`，统一执行 host tests、Markdown 与图检查；完整固件构建由独立 [Firmware-build workflow](../.github/workflows/firmware-build.yml) 执行。

原始构建、串口日志和中间产物只作为本地、CI 或 Release artifact 临时保存；影响判定的事实先提炼到对应 records，再删除临时产物。
