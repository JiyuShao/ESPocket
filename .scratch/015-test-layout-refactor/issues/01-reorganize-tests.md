# 01 — 调整测试目录与设备执行职责

**What to build:** 实施用户同意的 Owner/host/device 布局，拆出设备测试入口、协议客户端、执行器与用例。

**Blocked by:** None.

**Status:** resolved

- [x] Owner 测试留在组件/App，跨模块主机测试迁到 host，Runtime 样例测试迁回 App。
- [x] 设备用例、客户端、执行器、profile 分离；旧 CLI 与参数兼容，无两份配置。
- [x] 主机默认发现排除设备套件；CLI 主机测试与迁移前后用例对比通过。
- [x] 全量主机与 Markdown 检查通过，新入口实际设备 navigation attempt 结果独立保存。
- [x] Firmware README、脚本说明与开发协议更新，历史证据不冒充本次结果。

## Comments

- 2026-10-02：用户要求整体实施此前目录与命名设计。此次仅调整测试工具，不重建或刷写固件，不新增人工轮次。

## Resolution

完整 host 与 CLI 检查通过；普通镜像的新入口 35 步 navigation PASS，release 成功。见 [证据](../records/2026-10-02-test-layout.md)。保持旧 CLI 参数/profile 兼容，未刷机、未追加人工验收、未 push。
