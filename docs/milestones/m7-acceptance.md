# M7 Navigation Surfaces 验收规范

## 状态

- M7: `NOT ENTERED`
- Dependency: M6 `PASS`
- M4–M5 may remain `BLOCKED`, but their blockers remain release gates

本文定义 M7 的范围与 PASS 门槛。实现必须遵守 [`../design/product/interaction-model.md`](../design/product/interaction-model.md)。

## 目标

在 M6 Home 与显示状态基础上，建立系统 Surface、Cards、Quick Settings 与 Native App Back 的完整导航闭环。

```text
Watch Face ↔ Cards
Watch Face → Quick Settings → Back → Watch Face
Watch Face → Launcher → App → Back → Launcher
Card → App → Back → Original Card
App Root → Detail → Back → App Root
Any Screen On Non-Home Surface → PWR → Watch Face
```

## Scope

- Watch Face 左右 Cards。
- Watch Face 下滑进入 Quick Settings。
- 左右任意屏幕边缘向内的 Edge Back。
- 单一直接 Launch Source，不建立跨 App 历史链。
- Launcher / Quick Settings Back → Watch Face。
- Native App Detail Back → Parent。
- Native App Root Back → Launch Source。
- Launch Source 失效时 Back → Watch Face。
- Watch Face 上 Back 为 no-op。
- Card 序列边界不循环。
- Card 打开 App 后 Back 恢复原 Card；PWR 仍回 Watch Face。
- Quick Settings 直接切换项立即生效并停留；复杂配置进入 Settings，Back 返回 Quick Settings。
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
| Card boundary | Card 单页、单主题；无内部 Detail 栈 | PASS（STATIC，dependency-gated） |
| Launch Source | 只记录一个直接来源；无任意历史链 | PASS（STATIC，dependency-gated） |
| Native Back | Detail → Parent；Root → Launch Source；失效 → Watch Face | PASS（HOST BUILD + STATIC，真机待验收） |
| Gesture ownership | Edge Back 不占用普通横滑；上下滑仍可滚动 | PASS（STATIC，真机待验收） |
| Existing services | Battery、Brightness、Wi-Fi、Settings 复用现有能力 | PASS（HOST BUILD + STATIC，真机待验收） |
| No premature framework | 无通用 Card SDK、插件框架或编辑器 | PASS（STATIC） |
| Build | 正常固件 clean build/link 成功 | PASS（2026-09-28，dependency-gated） |
| Static checks | JSON、脚本或项目既有检查全部通过 | PASS（JSON parse + `git diff --check`） |

## Hardware Acceptance

真机证据是 M7 PASS 的必要条件。

### Fixed repetition counts

以下完整系统导航闭环执行 5 次。任何一次失败都必须记录，不能追加次数稀释失败。

```text
Watch Face
 → Card boundaries
 → Battery Card
 → Brightness Card / immediate action
 → Watch Face
 → Quick Settings / direct actions
 → Settings
 → Back to Quick Settings
 → Back to Watch Face
 → Launcher
 → Native App Root
 → Detail
 → Back to Root
 → Back to Launcher
 → PWR to Watch Face
```

| 检查项 | 次数 | PASS 条件 | 状态 |
|---|---:|---|---|
| Complete navigation loop | 5 | 每轮来源恢复、Back 与 Home 均正确 | NOT TESTED |
| Wi-Fi real toggle | 5 | 状态真实生效并保持在 Quick Settings | NOT TESTED |
| Brightness real change | 5 | 显示亮度真实变化并保持在当前 Surface | NOT TESTED |

### Required path coverage

每条路径至少单独覆盖一次：

| 路径 | PASS 条件 | 状态 |
|---|---|---|
| Watch Face ↔ Cards | 顺序稳定，边界不循环 | NOT TESTED |
| Watch Face → Quick Settings → Back | 返回 Watch Face | NOT TESTED |
| Launcher → App Root → Back | 返回 Launcher | NOT TESTED |
| Card → App Root → Back | 返回原 Card | NOT TESTED |
| App Root → Detail → Back | 返回 App Root | NOT TESTED |
| Quick Settings → Settings → Back | 返回 Quick Settings | NOT TESTED |
| Watch Face + Edge Back | no-op | NOT TESTED |
| Normal horizontal swipe in App | 由 App 处理，不误触发 Back | NOT TESTED |
| Any Screen On non-Home + PWR | 返回 Watch Face | NOT TESTED |
| Failure scan | 无 panic、watchdog、assert、错误 Back 或错误来源恢复 | NOT TESTED |

## Evidence Rules

- 每轮必须标识 attempt 编号和所有关键来源/目标。
- Quick Settings 的 Wi-Fi 与 Brightness 必须证明真实系统状态变化，不能只验证控件文本。
- Card → App → Back 必须证明恢复的是启动该 App 的原 Card。
- 物理触摸与显示观察不可由日志或 Preview 代替。
- 任一必须项缺少证据时不得标记 M7 `PASS`。

## Result

`NOT ENTERED`

M7 源码已按项目所有者授权提前开发，并通过主机构建与静态检查；记录见 [`evidence/m7-m8/M7_M8_HOST_BUILD_2026-09-28.txt`](evidence/m7-m8/M7_M8_HOST_BUILD_2026-09-28.txt)。由于 M6 尚未 `PASS`，M7 仍保持 `NOT ENTERED`，所有真机项保持 `NOT TESTED`。
