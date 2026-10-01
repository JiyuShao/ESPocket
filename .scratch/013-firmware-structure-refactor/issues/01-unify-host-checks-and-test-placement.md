# 01 — 统一 host checks 与测试位置

**What to build:** 建立只读的 `python3 scripts/check.py` 聚合入口，并把现有结构断言放入与 Owner 一致的 ESP-IDF 测试目录。

**Blocked by:** 当前 Home Space、PWR 与 test-automation 工作已稳定并提交。

**Status:** ready-for-agent

- [ ] Component 自有断言位于 component 的 `test/`，跨 component 断言位于 `firmware/test/`。
- [ ] 现有 Shell document action 结构测试迁入 `shell_circular/test/` 且继续通过。
- [ ] `python3 scripts/check.py` 统一执行无需硬件、无需完整 ESP-IDF build 的确定性检查。
- [ ] 聚合入口只读，不格式化、修复或覆盖工作区文件；需要生成时在临时目录比较。
- [ ] 检查拒绝受版本控制的 build、managed、Board Manager 与 Runtime App 本地产物。
- [ ] 本 ticket 不改变固件运行行为。
