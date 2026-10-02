# 仓库脚本

无需硬件的统一验证入口是 `python3 scripts/check.py`。默认运行 Markdown、离线 parser 与各 Owner 的 host tests；`--diagrams` 显式增加 Node／Chrome 图检查。编译和测试生成物只放入临时目录，固件构建与真机验收独立执行。

仓库自有操作入口统一放在 `scripts/`，按责任分组；测试用例与支撑实现归对应 Owner 或 `firmware/test/`，生成结果写入各入口指定的产物目录。

| 目录 | 责任 | 主要入口 |
|---|---|---|
| `docs/` | 文档结构、架构图生成与布局验证 | `python3 scripts/docs/check.py` |
| `tracker/` | 本地 Markdown tracker 的 Sequence 分配与脚手架 | `python3 scripts/tracker/new-effort.py` |
| `firmware/` | firmware 日志验证与目标板诊断 | `verify_m2_lifecycle.py`、`diagnose_syscore_boot.py`、`run_device_tests.py` |

`scripts/docs/generate-architecture-diagrams.mjs` 默认写入 `docs/design/architecture/assets/`。`scripts/docs/check.py` 使用临时输出重新生成并比较，不直接改写已提交 SVG。

设备诊断脚本可能需要串口设备、`pyserial`、`esptool` 和对应硬件授权；离线 parser self-test 不需要连接设备。

`firmware/prepare_host_dependencies.py` 是显式的 host 环境准备命令，通过官方 Component Manager 物化锁定 Settings 测试资源；它不属于只读检查入口。

`firmware/run_device_tests.py` 在明确的设备开发者模式、镜像 identity 和输入 profile 下运行 USB 合成输入；协议、CLI、失败清理与证据分类见 [开发协议](../docs/development/interaction-test-protocol.md)。Driver 输出为独立 attempt 的临时报告与原始日志，不提交源码树，不替代物理或视觉验收。

设备测试用例与支撑代码位于 `firmware/test/device/`，本目录只保留 CLI 入口。目录分工与主机发现规则见 [Firmware 测试说明](../firmware/README.md)。旧 `interaction_driver.py` 保留为 CLI 兼容入口。
