# 01 — 统一 host checks 与测试位置

**What to build:** 建立只读的 `python3 scripts/check.py` 聚合入口，并把现有结构断言放入与 Owner 一致的 ESP-IDF 测试目录。

**Blocked by:** None — 当前行为基线已提交为 `43159fb`。

**Status:** resolved

- [x] Component 自有断言位于 component 的 `test/`，跨 component 断言位于 `firmware/test/`。
- [x] 现有 Shell document action 结构测试迁入 `shell_circular/test/` 且继续通过。
- [x] `python3 scripts/check.py` 统一执行无需硬件、无需完整 ESP-IDF build 的确定性检查。
- [x] 聚合入口只读，不格式化、修复或覆盖工作区文件；需要生成时在临时目录比较。
- [x] 检查拒绝受版本控制的 build、managed、Board Manager 与 Runtime App 本地产物。
- [x] 本 ticket 不改变固件运行行为。

## Resolution

2026-10-02：迁移四个自有 component 测试并建立跨 component 目录断言，统一只读 host 入口通过，完整固件构建通过；运行行为未改动。详见 [阶段记录](../records/2026-10-02-host-checks.md)。
