# 03 — 完成系统导航真机验收

**What to build:** Cards、Quick Settings、子页面 Back、Root 无 Back、PWR Home、gesture 与真实 Wi-Fi/brightness 效果的真机证明。

**Blocked by:** [006/03 Home 与显示真机验收](../../006-m6-home-display/issues/03-run-hardware-acceptance.md)（已完成）；[02 导航源码与构建](02-close-navigation-source-gates.md)。

**Status:** ready-for-human

- [x] 完整导航闭环通过 2 次（样机镜像；见[两轮记录](../records/2026-10-02-two-navigation-loops.md)）。
- [x] Wi-Fi 与 brightness 各自真实改变状态 2 次（采集窗口累计；见[两轮记录](../records/2026-10-02-two-navigation-loops.md)）。
- [ ] 所有单次 source、gesture、Home 与 failure 检查通过。

## Comments

- 2026-10-01：原任务包含「Back、直接 Launch Source」真机证明。根据 [ADR-0011](../../../docs/adr/0011-app-root-has-no-back.md)，改为子页面 Back、Root 无 Back 与 PWR Home；原要求保存在此作为决策历史。
- 2026-10-02：用户在多轮操作均正常后要求减少重复验收。固定次数从 5 降为 2，证据见 [两轮记录](../records/2026-10-02-two-navigation-loops.md)；单次路径覆盖与最终镜像核对仍保留。

## 真机步骤与逐项结果

本票全部必需项通过后才能关闭；真机证据是必要条件。

### Fixed repetition counts

以下完整系统导航闭环执行 2 次。任何一次失败都必须记录，不能追加次数稀释失败。原门槛为 5 次；2026-10-02 用户在多轮真机操作均正常后要求降低重复次数，故将三项固定重复门槛同步改为 2 次，单次路径覆盖仍保留。

```text
Watch Face
 → Card boundaries
 → Battery Card
 → Brightness Card / immediate action
 → Watch Face
 → Quick Settings / direct actions
 → Up to Watch Face
 → Launcher
 → Native App Root
 → Detail
 → Back to Root
 → PWR to Watch Face
```

| 检查项 | 次数 | PASS 条件 | 状态 |
|---|---:|---|---|
| Complete navigation loop | 2 | 每轮 Home Space 手势、App 子页面 Back 与 PWR Home 均正确 | PASS（2/2，样机镜像；[记录](../records/2026-10-02-two-navigation-loops.md)） |
| Wi-Fi real toggle | 2 | 状态真实生效并保持在 Quick Settings | PASS（2/2，样机镜像；[记录](../records/2026-10-02-two-navigation-loops.md)） |
| Brightness real change | 2 | 显示亮度真实变化并保持在当前 Surface | PASS（至少 2 次，样机镜像；[记录](../records/2026-10-02-two-navigation-loops.md)） |

### Required path coverage

每条路径至少单独覆盖一次：

| 路径 | PASS 条件 | 状态 |
|---|---|---|
| Watch Face ↔ Cards | 顺序稳定，边界不循环 | PARTIAL（Battery/Brightness 往返已见，序列边界未单测） |
| Watch Face → Quick Settings → Up | 返回 Watch Face | PASS（样机镜像） |
| Watch Face → Launcher → top pull release | 返回 Watch Face，不误开 App | NOT TESTED |
| Launcher → App Root → Edge Back | 保持 App Root，无返回控件 | PASS（样机镜像；[记录](../../014-app-navigation-card-contract/records/2026-10-02-default-back-prototype.md)） |
| App Root → Detail → Back | 返回 App Root | PASS（样机镜像；[记录](../../014-app-navigation-card-contract/records/2026-10-02-default-back-prototype.md)） |
| Quick Settings → Settings Root → PWR | 返回 Watch Face | NOT TESTED |
| Normal horizontal swipe in App | 由 App 处理，不误触发 Back | NOT TESTED |
| Any Screen On non-Home + PWR | 返回 Watch Face | PARTIAL（Native Root/Detail 已见，其他 Surface 未覆盖） |
| Failure scan | 无 panic、watchdog、assert 或错误 Back | PARTIAL（本次串口窗口未见，最终镜像仍待核对） |

## 证据规则

- 每轮必须标识 attempt 编号和所有关键页面与目标。
- Quick Settings 的 Wi-Fi 与 Brightness 必须证明真实系统状态变化，不能只验证控件文本。
- App Root 必须证明无可见 Back；PWR Home 必须证明直接回 Watch Face。
- 物理触摸与显示观察不可由日志或 Preview 代替。
- 任一必需项缺少证据时不得关闭本票。
