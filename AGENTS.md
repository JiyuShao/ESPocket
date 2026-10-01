# ESPocket Agent 指南

## Agent 工作入口

### Issue tracker

Spec 与 ticket 以版本化 Markdown 保存在 `.scratch/`。规则见 [issue tracker 指南](docs/agents/issue-tracker.md)。

### Triage labels

使用五个规范 Matt triage role。定义见 [triage labels](docs/agents/triage-labels.md)。

### Domain docs

本仓库使用单一 context。修改某个领域前，先阅读 `CONTEXT.md` 和 `docs/adr/` 中的相关记录。读取顺序见 [domain docs](docs/agents/domain.md)。

## 文档工作流

按照 `docs/README.md` 将每类含义写入对应权威位置。工作范围与状态写入 `.scratch/<effort>/spec.md`；可执行工作、依赖与验收条件写入 `issues/`；有日期的证据与历史结果写入同一 Effort 的 `records/`。

修改文档后运行 `python3 scripts/docs/check.py --markdown`。
修改架构 SVG、图生成器或图布局检查器后，另运行 `python3 scripts/docs/check.py --diagrams`；CI 通过 `python3 scripts/check.py --diagrams` 执行统一检查。

修改 firmware 源码、资源或结构后运行 `python3 scripts/check.py`；完整构建与真机验收按对应 ticket 独立执行。Host checks 的环境准备与目录规则见 [Firmware README](firmware/README.md)。
