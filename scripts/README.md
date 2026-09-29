# 仓库脚本

仓库自有自动化统一放在 `scripts/`，按责任分组；生成结果仍写回其所属的产品或文档目录。

| 目录 | 责任 | 主要入口 |
|---|---|---|
| `docs/` | 文档结构、架构图生成与布局验证 | `python3 scripts/docs/check.py` |
| `tracker/` | 本地 Markdown tracker 的 Sequence 分配与脚手架 | `python3 scripts/tracker/new-effort.py` |
| `firmware/` | firmware 日志验证与目标板诊断 | `verify_m2_lifecycle.py`、`diagnose_syscore_boot.py` |

`scripts/docs/generate-architecture-diagrams.mjs` 默认写入 `docs/design/architecture/assets/`。`scripts/docs/check.py` 使用临时输出重新生成并比较，不直接改写已提交 SVG。

设备诊断脚本可能需要串口设备、`pyserial`、`esptool` 和对应硬件授权；离线 parser self-test 不需要连接设备。
