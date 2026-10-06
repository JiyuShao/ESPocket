# 03 — 实施 Overlay 输入与期限规则

**What to build:** 在现有 Core 请求与 Shell 呈现关系上落实 INT-028–032 和 ADR-0017。

**Blocked by:** [018/01 规则确认](../../018-system-super-reference-audit/issues/01-audit-system-and-shell.md)（已完成）；[005/07 Runtime 隔离](../../005-m5-application-ecosystem/issues/07-isolate-runtime-keyboard-results.md)（已完成）。

**Status:** ready-for-agent

- [ ] 确认弹窗优先于键盘，键盘保留草稿并暂停输入；弹窗结束只恢复仍有效的原请求，Loading 优先级最低。
- [ ] 键盘 Back 取消输入，不 pop 底层 App Page；覆盖默认按钮和 Edge Back。
- [ ] 同周期 PWR 优先于未提交选择；已提交操作按 Owner 结果核实，不报告为已撤销。
- [ ] Home 后系统提示可继续呈现；Watch Face PWR 仍息屏；息屏只暂停呈现自动关闭计时，操作/授权/Owner 期限继续有效。
- [ ] 覆盖重叠/更新、Home/息屏/唤醒、请求失效、迟到结果、GUI hide/锁失败及停止中的 userdata/callback 安全。
- [ ] 有真实竞争边界回归、统一检查、独立完整构建与新增真机输入/显示路径证据；不以 LVGL 创建顺序代替规则。

## Execution Notes

不复制 Core Dialog 队列，不新增通用 Overlay 生命周期管理器。02 持有全量 System 重复运行；本票持有 Overlay 请求完成、隐藏及失效的实际结果。

## Comments

2026-10-04：隔离副本已实施 Shell 仲裁、键盘 Back、PWR 提交边界、呈现计时暂停与失败隐藏/userdata 保留，并完成实际 C++ 控制流回归。详见[隔离实施记录](../records/2026-10-04-overlay-isolated-implementation.md)。原 checkout 未整合；统一检查有继承的 Store 夹具失败，完整构建与设备门槛分别记录。保留 ready-for-agent 与全部整体验收条件，不能写成已关闭。


2026-10-05：隔离交付已三方整合入当前 checkout；新增 Core 补丁按当前组合重新准确应用，整合中两处空 Overlay 重试回归已修复。联合 host checks、构建和设备结果见[联合整合记录](../records/2026-10-05-joint-integration.md)。此前隔离阶段记录保留；本票未满足的条件继续开放。
