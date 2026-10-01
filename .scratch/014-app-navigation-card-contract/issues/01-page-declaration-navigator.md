# 01 — 声明与 App Page Navigator

**What to build:** 在 ESPocket 产品层校验 App Root、全部 Page ID 与可选 Card 目标，提供执行模型无关的唯一 Page 栈和 Native 接入；Runtime 语言绑定留给 ticket 04。

**Blocked by:** M6 `PASS`；该 ticket 是 M7 Native Back source gate 的前置工作。

**Status:** ready-for-agent

- [ ] 无 Root、重复 ID 或 Card 指向未声明 Page 时安装校验失败；声明身份在 App 更新后稳定。
- [ ] Root 不可 pop，运行时未知 Page 不修改原栈；Card 目标运行时失效降级 Root 并记录错误。
- [ ] PWR Home 后再打开从 Root 开始，息屏唤醒保留有效 Page，实例失效清除旧栈。
- [ ] Navigator 从同一状态给出当前 `pageId`、`canBack`、`backPending`，不暴露参数或整条栈。
- [ ] Navigator 接口不依赖 Native GUI 实现细节；Native Adapter 对操作和错误使用该接口，Runtime Adapter 留给 ticket 04。

## Comments

- 2026-10-02：原最后一项要求 Native 与 Runtime Adapter 同时完成，与 M7 Native source gate → M8 Runtime 验收顺序冲突。当前 ticket 先提供共同 Navigator 和 Native 接入；Runtime Adapter 的对等验证移到 ticket 04，保留共同语义目标。
- 2026-10-02：已加入执行模型无关的 `PageNavigator`、Native 示例 Page 声明与画面适配，主机接口测试覆盖声明错误、Root、push/pop、Card 直达与目标缺失、停止重启和呈现失败。Native 真机路径、App 更新时 ID 迁移与运行时诊断仍待验证；见 [M7 记录](../../../docs/milestones/m7/records/2026-10-02-page-navigator-source.md)。
