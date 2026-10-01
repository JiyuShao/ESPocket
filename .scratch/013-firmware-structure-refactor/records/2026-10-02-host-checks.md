# 结构重构第一阶段：统一 host checks

- 日期：2026-10-02
- 范围：013/01
- 重构前固定基线：`43159fb`

## 变更

四个自有 component 的现有 `tests/` 全部迁入 `test/`，保留原有断言。Navigator 和 USB protocol 的 C++ 行为测试增加 Python unittest 执行入口，在临时目录编译真实源码。Settings 的 CMake 配置兼容门槛同步到新路径。

跨 component 的目录边界测试位于 `firmware/test/`，检查受控文件中没有 build、managed components、Board Manager 输出、本地 sdkconfig 或 Runtime App 的 build/dist/node_modules。负例覆盖当前与目标 App 目录，并保留 dependencies.lock 和 sdkconfig.defaults 的合法性。

`python3 scripts/check.py` 聚合 Markdown、离线 M2 parser self-test 和所有自有 component／跨 component host tests。默认不运行 Chrome；`--diagrams` 显式增加现有图检查。它不自动修复、格式化或覆盖工作区，C++ 中间产物仅存在于临时目录。

## 验证

- 统一入口通过：Markdown、M2 parser、Navigator 1 项、Settings 2 项、USB protocol 1 项、Shell document 1 项、跨 component 3 项。
- 执行前后源码和文档内容 hash 比较一致，证明当前检查未改写这些工作区文件。
- 完整 ESP-IDF build 通过；迁移后的 Settings CMake 配置门槛通过。
- 构建目录：`/private/tmp/espocket-m78-build`，日志作为本地临时产物保存于 `/private/tmp/espocket-refactor-01-build.log`。
- 本阶段未改动固件运行源码，也未刷机或新增真机通过项。既有验收结果保留；后续 ShellHost／PWR Owner 改动仍需按 04 统一 smoke。

## 后续

013/02 抽离 Shell 与 Hello Native GUI 资源，并比较声明、订阅与 handler action 集合。CI 收敛仍由 013/06 持有。
