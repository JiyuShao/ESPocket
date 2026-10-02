# 04 — 解决 Runtime 异步 GUI 栈溢出

**What to build:** 在保持 Runtime 导航、确认提示与公开开发 API 的前提下，解决真实 RuntimeJsAsync 栈溢出并通过设备回归。

**Blocked by:** 锁定 backend 0.8.3 固定 8 KiB 异步任务栈且无公开配置；需上游公开配置/执行能力修复，或用户另行决定源码维护策略。不能改 managed_components 或删掉产品行为作为验收。

**Status:** needs-info

- [ ] 确定受支持的上游修复或配置机制及锁定版本。
- [ ] 保留确认开关与待决反馈，runtime-confirm 最小设备回归通过。
- [ ] apps 完整 Native/Runtime 套件与实际物理检查通过。
- [ ] 恢复普通镜像，记录资源 identity、失败和修复后的独立 attempt。

## Comments

2026-10-02：008/03 的真实 apps attempt 在 Runtime confirmation On 重启。无需息屏的最小路径同样失败；仅省略异步文字调用的诊断资源使路径通过，但不接受为正式修复。见[上游复现](../../../docs/upstream/issues/runtime-js-async-stack-overflow.md)与[设备记录](../records/2026-10-02-app-device-frontier.md)。

2026-10-03：确认此前 backend 版本误记，实际 JS 0.8.3/Manager 0.8.2，镜像和复现事实不变。已准备[公开栈配置补丁提案](../records/2026-10-03-runtime-stack-proposal.md)，尚待用户决定组件补丁维护策略，不自行修改正式依赖。
