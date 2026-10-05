# 04 — 从 Core 投影 dynamic Launcher entry

**What to build:** 可信 dynamic App 根据完整 Core snapshot 在 Launcher 中出现和消失，同时固定 entry 保持稳定。

**Blocked by:** [03 Core package trust](03-enforce-core-package-trust.md)；[06 在线 Store 修复复验](06-adopt-online-store-stability-fix.md)；[07 Runtime keyboard isolation](07-isolate-runtime-keyboard-results.md)。

**Status:** ready-for-agent

- [x] Launcher 以 Core committed state 作为唯一 dynamic source。
- [x] Notification 丢失或合并后，可通过 full reconciliation 恢复。
- [x] Refresh 失败时保留上一份完整 projection。
- [x] Launch 根据 manifest identity 解析当前 runtime identity。

## 从原 policy 恢复的 Implementation Decisions

- 固定产品 entry 保留在 Shell document 中，dynamic reconciliation 不能删除、重排或遮蔽它们。
- Dynamic eligibility 要求 App 是可见 Runtime App、不在 fixed manifest set、trust admission 成功，并出现在 Core committed list。
- Install/uninstall hook 只推进 dirty generation。Hook 返回后，由 Shell 持有、运行在 App task 的 timer 读取完整 snapshot；Shell start 为 reboot discovery 执行首次 reconciliation。
- Dynamic region 使用现有 JSON UI template API。Instance identity 是 manifest identity 的确定性、带 collision check 的 digest，不使用 `std::hash`；in-memory mapping 从 Core 重建。
- Entry 按 Core 解析的 localized display name 与 manifest identity 排序。缺失 icon 时回退为文本；icon preload 遵循 view lifetime。
- 一个共享 dynamic Action 从 event path 记录 manifest identity。App-task dispatcher 再次列出 App、重新检查 eligibility、解析当前 `AppId`、只启动一次并清除 intent。
- Reconciliation 构建 replacement subtree，所有 view ready 后才 swap。失败时销毁临时 subtree、保留上一完整 view，并以 log rate limiting 重试。

## Required matrix

- [x] 过滤 hidden、Native、fixed、incompatible 与 untrusted App。
- [x] 覆盖 deterministic sorting、name fallback、instance collision 与 icon fallback。
- [x] 合并重复 notification，不产生重复 entry。
- [x] 更新 metadata 时不复制 identity，并 dispatch 到新 `AppId`。
- [x] 拒绝 click/uninstall race，并取消已移除的 pending target。
- [x] Shell restart 后重建，不持久化 Launcher state。
- [x] 每次 reconciliation failure 中固定 entry 都保持可用。
- [ ] 当前正常镜像完成 Store 安装／卸载对应的 Launcher 增减、启动与重启发现真机回归；前置 06 完整稳定性门槛已通过。

## Comments

2026-10-04：用户授权全部剩余项。动态开发者条目沿用 ADR-0018 的 Core 准入结果；普通发行仍依赖 08，不把例外提升为发行信任。Core 完整列表和正式 start gate 为唯一事实源，安装 hook 只触发重建；现在实施和验收本票。

2026-10-04 主机矩阵与真实 Shell Owner GUI fault harness 全部通过，普通候选 `0116972e3` 已有 Flappy 动态行截图、实际启动与 PWR Home；实现条件勾选，剩余当前镜像完整 lifecycle 及 06 设备门槛独立保留。证据见[自动验收记录](../records/2026-10-04-launcher-and-lifecycle-acceptance.md)。
