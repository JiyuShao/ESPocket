# 04 — 解决 Runtime 异步 GUI 栈溢出

**What to build:** 在保持 Runtime 导航、确认提示与公开开发 API 的前提下，解决真实 RuntimeJsAsync 栈溢出并通过设备回归。

**Blocked by:** 无；源码、完整构建、自动设备、有限资源与物理条件均已完成。

**Status:** resolved

- [x] 确定受支持的上游修复或配置机制及锁定版本：用户接受 ADR-0015 的限定源码补丁方案，锁定 JS 0.8.3。
- [x] 保留确认开关与待决反馈，runtime-confirm 最小设备回归通过（普通 c8d56e5e2，synthetic-input，视觉待单独验收）。
- [x] apps 完整 Native/Runtime 套件与实际物理检查通过。
- [x] 恢复普通镜像，记录资源 identity、失败和修复后的独立 attempt。

## Comments

2026-10-02：008/03 的真实 apps attempt 在 Runtime confirmation On 重启。无需息屏的最小路径同样失败；仅省略异步文字调用的诊断资源使路径通过，但不接受为正式修复。见[上游复现](../records/2026-10-02-runtime-js-async-stack-overflow.md)与[设备记录](../records/2026-10-02-app-device-frontier.md)。

2026-10-03：确认此前 backend 版本误记，实际 JS 0.8.3/Manager 0.8.2，镜像和复现事实不变。已准备[公开栈配置补丁提案](../records/2026-10-03-runtime-stack-proposal.md)，尚待用户决定组件补丁维护策略，不自行修改正式依赖。

2026-10-03：完成[独立组件副本准备工具](../records/2026-10-03-patch-preparation-tool.md)，通过实际锁定版源码与补丁准备验证。发现 ADR-0001 的产品基线限制，已提出限定例外确认；尚未接入正式构建或宣称设备修复。

2026-10-03：用户回复「好，不要停，我去休息了，你把能做的都做了吧」，接受此前明确询问的 ADR-0001 限定例外。正式补丁及独立工程构建入口已实现，先验证 16 KiB；测试结果另行追加，不预先判定修复。

2026-10-03：正式接入的准备失败、锁定与主机结果见[补丁验证](../records/2026-10-03-runtime-stack-patch-validation.md)；真实设备结果按同一记录独立追加。

2026-10-03：普通最小/完整 apps、两种独立 reclaim 及有限资源路径均通过；已恢复普通 c8d56e5e2。剩余物理/视觉检查集中留给用户休息后一次执行。

## Resolution

2026-10-03：锁定 JS 0.8.3 的 16 KiB 异步栈补丁通过准确应用、clean build、Runtime 最小/完整套件、两种独立回收与有限资源检查；用户确认 Runtime On/pending/Cancel、息屏恢复及完整回收路径，确认反馈未删减。当前普通固件 57 步 PASS，普通镜像恢复正常。原栈溢出与采集缺项保留；详细物理证据见[当前固件验收](../records/2026-10-03-current-firmware-acceptance.md)，不保证任意未来 App 栈上界。
