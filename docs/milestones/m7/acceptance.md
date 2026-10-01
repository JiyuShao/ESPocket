# M7 Navigation Surfaces 验收规范

> 文档类型：固定阶段门槛与当前判定。实施计划和 tickets 位于 `.scratch/007-m7-navigation/`。

## 状态

- M7: `IN PROGRESS`（2026-10-02，M6 `PASS` 后进入）
- Dependency: M6 `PASS`
- M4–M5 may remain `BLOCKED`, but their blockers remain release gates

本文定义 M7 的范围与 PASS 门槛。实现必须遵守[系统交互模型](../../design/product/03-interaction-model.md)。

## 目标

在 M6 Home 与显示状态基础上，建立系统 Surface、Cards、Quick Settings 与 Native App Back 的完整导航闭环。

```text
Watch Face ↔ Cards
Watch Face → Quick Settings → 上滑 → Watch Face
Watch Face → Launcher → App Root → PWR → Watch Face
App Root → Detail → Back → App Root
Any Screen On Non-Home Surface → PWR → Watch Face
```

## Scope

- Watch Face 左右 Cards。
- Watch Face 下滑进入 Quick Settings。
- Home Space 周边页反向滑动返回 Watch Face；Launcher 到顶后下拉越过阈值并松手返回。
- 完整 App 子页面默认有可见 Back 与 Edge Back；Root 无 Back。App 可同时关闭默认入口，多级 App 必须自带可见 Back。
- Launcher 下拉、Quick Settings 上滑 → Watch Face。
- Native App Detail Back → Parent。
- Native App Root 无可见 Back，Edge Back 不执行导航。
- Card 序列边界不循环。
- Quick Settings 直接切换项立即生效并停留；进入 Settings 后遵守 App Page 栈规则。
- PWR Home 覆盖上述普通导航。

## Minimum Real Content

只实现足以验证交互模型的真实内容：

- 只读 Card：Battery。
- 即时操作 Card：Brightness。
- Quick Settings：Brightness、Wi-Fi、Battery 状态、Settings 入口。
- 一个 Native App Root / Detail 路径。

优先复用现有 Battery、Brightness、Wi-Fi 与 Settings 能力。

## Out of Scope

- Runtime App 的统一 Back 合同；留给 M8。
- Bluetooth、Sound、Do Not Disturb、Lock、Music 和 Notifications。
- 通用 Card SDK、插件框架或 Card 编辑器。
- Card 排序 UI；首版使用固定默认顺序。
- 动态 Launcher 与不可信 Runtime package exposure。
- 任意 App-to-App 返回链。
- 手势阈值、竞争优先级或识别算法的产品规定。

## Source / Build Gates

| 检查项 | PASS 条件 | 状态 |
|---|---|---|
| Surface model | Home Space、Launcher、Quick Settings 与 App Surface 关系符合主规范 | PASS（STATIC，dependency-gated） |
| Card boundary | 当前固定 Shell Card 为单页内容；未来 App Card 遵守专门的呈现与导航契约 | OPEN（新契约待复核，dependency-gated） |
| Native Back | Detail → Parent；Root 无 Back；PWR Home → Watch Face | OPEN（新契约待实现与真机验收） |
| Gesture ownership | Home Space 反向滑动、Launcher 顶部下拉、App 默认 Back 不占用普通滚动和横滑 | OPEN（新手势待真机验收） |
| Existing services | Battery、Brightness、Wi-Fi、Settings 复用现有能力 | PARTIAL（2026-10-02，Shell Brightness OutputId 已按真实输出修复并构建；真实亮度变化及其他能力仍需真机验收） |
| No premature framework | 无通用 Card SDK、插件框架或编辑器 | PASS（STATIC） |
| Build | 正常固件 clean build/link 成功 | PASS（2026-10-02，隔离目录构建；[记录](records/2026-10-02-brightness-output-id.md)） |
| Static checks | JSON、脚本或项目既有检查全部通过 | PASS（JSON parse + `git diff --check`） |

## Hardware Acceptance

真机证据是 M7 PASS 的必要条件。

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
| Complete navigation loop | 2 | 每轮 Home Space 手势、App 子页面 Back 与 PWR Home 均正确 | PASS（2/2，样机镜像；[记录](records/2026-10-02-two-navigation-loops.md)） |
| Wi-Fi real toggle | 2 | 状态真实生效并保持在 Quick Settings | PASS（2/2，样机镜像；[记录](records/2026-10-02-two-navigation-loops.md)） |
| Brightness real change | 2 | 显示亮度真实变化并保持在当前 Surface | PASS（至少 2 次，样机镜像；[记录](records/2026-10-02-two-navigation-loops.md)） |

### Required path coverage

每条路径至少单独覆盖一次：

| 路径 | PASS 条件 | 状态 |
|---|---|---|
| Watch Face ↔ Cards | 顺序稳定，边界不循环 | PARTIAL（Battery/Brightness 往返已见，序列边界未单测） |
| Watch Face → Quick Settings → Up | 返回 Watch Face | PASS（样机镜像） |
| Watch Face → Launcher → top pull release | 返回 Watch Face，不误开 App | NOT TESTED |
| Launcher → App Root → Edge Back | 保持 App Root，无返回控件 | PASS（样机镜像；[记录](records/2026-10-02-default-back-prototype.md)） |
| App Root → Detail → Back | 返回 App Root | PASS（样机镜像；[记录](records/2026-10-02-default-back-prototype.md)） |
| Quick Settings → Settings Root → PWR | 返回 Watch Face | NOT TESTED |
| Normal horizontal swipe in App | 由 App 处理，不误触发 Back | NOT TESTED |
| Any Screen On non-Home + PWR | 返回 Watch Face | PARTIAL（Native Root/Detail 已见，其他 Surface 未覆盖） |
| Failure scan | 无 panic、watchdog、assert 或错误 Back | PARTIAL（本次串口窗口未见，最终镜像仍待核对） |

## Evidence Rules

- 每轮必须标识 attempt 编号和所有关键页面与目标。
- Quick Settings 的 Wi-Fi 与 Brightness 必须证明真实系统状态变化，不能只验证控件文本。
- App Root 必须证明无可见 Back；PWR Home 必须证明直接回 Watch Face。
- 物理触摸与显示观察不可由日志或 Preview 代替。
- 任一必须项缺少证据时不得标记 M7 `PASS`。

## Result

`IN PROGRESS`（2026-10-02）

[2026-09-30 Home Space 交互样机](records/2026-09-30-home-space-prototype.md)是阶段外探索记录，不计入上方 M7 验收项。

M7 源码已按项目所有者授权提前开发，并通过主机构建与静态检查。在 M6 尚未 `PASS` 时，M7 保持 `NOT ENTERED`，所有真机项未计入正式验收。

2026-10-01：导航契约由 [ADR-0011](../../adr/0011-app-root-has-no-back.md) 改为 Root 无 Back。此前针对 Root Back → Launch Source 的静态 PASS 只证明旧实现，不能计入新 Native Back gate；新 gate 为 `OPEN`，真机项仍为 `NOT TESTED`。完整 App Card 机制仍在 M7 范围外。

当前工作树固件已重新完成隔离构建；该结果不解除 M6 依赖或真机门槛。

2026-10-02：[M6 已通过](../m6/acceptance.md)，M7 进入 `IN PROGRESS`。上方仍为 `OPEN` 或 `NOT TESTED` 的项目需要按本页门槛实施与取证；阶段进入不等于 M7 通过。

2026-09-29 本地源码复核发现，当时 Shell Brightness 读写固定传 `OutputId = 0`，而锁定版 Display Service 从 `1` 分配输出 ID，亮度函数按 ID 精确查找。因此此前的主机构建和静态检查不能证明 M7 亮度路径可用；M4 对官方 Settings App 的物理亮度验收也不覆盖 Shell 按钮。该问题已由[2026-10-02 修复](records/2026-10-02-brightness-output-id.md)处理，随后在[两轮样机记录](records/2026-10-02-two-navigation-loops.md)中观察到真实背光变化。

2026-10-02：[默认 Back 样机](records/2026-10-02-default-back-prototype.md)和[两轮导航记录](records/2026-10-02-two-navigation-loops.md)覆盖了部分真机门槛。触控测试所用镜像为 `8c5a877b...`；随后源码加入 Navigator 并发同步，新镜像 `03edef4c...` 已刷入并完成自动启动检查，但未要求用户重做重复触控。上表未通过的路径与新镜像的物理交互核对仍使 M7 保持 `IN PROGRESS`。
