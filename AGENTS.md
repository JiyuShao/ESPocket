# ESPocket Agent 指南

## Agent 工作入口

### Issue tracker

Spec 与 ticket 以版本化 Markdown 保存在 `.scratch/`。规则见 [issue tracker 指南](docs/agents/issue-tracker.md)。

### Triage labels

使用五个规范 Matt triage role。定义见 [triage labels](docs/agents/triage-labels.md)。

### Domain docs

本仓库使用单一 context。修改某个领域前，先阅读 `CONTEXT.md` 和 `docs/adr/` 中的相关记录。读取顺序见 [domain docs](docs/agents/domain.md)。

## 文档工作流

按照 `docs/README.md` 将每类含义写入对应权威位置。实施计划和可执行工作写入 `.scratch/`；状态与证据写入 `docs/milestones/`。

修改文档后运行 `python3 scripts/docs/check.py`。
