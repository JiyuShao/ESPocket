# M8 App Interaction Contract 验收规范

## 状态

- M8: `NOT ENTERED`
- Native / Contract dependency: M7 `PASS`
- Runtime validation dependency: M3 `PASS`
- M8 cannot become `PASS` until both dependency branches and all required evidence pass

本文定义 M8 的范围与 PASS 门槛。实现和 App 指导必须遵守 [`../design/product/interaction-model.md`](../design/product/interaction-model.md)。

## 目标

把 M7 已验证的系统与 Native 导航规则扩展为 Native App、Runtime App 和第三方 App 共用的稳定交互契约。

## Scope

- Native 与 Runtime App 使用一致的 Root / Detail / Back 模型。
- App Root Back 返回一个直接 Launch Source；来源失效时回 Watch Face。
- PWR Home、息屏、唤醒和回收降级对两种执行模型一致。
- App 可以使用 Tap、Scroll、普通横滑和 Long Press。
- 系统保留 PWR Home 与 Edge Back。
- Home 后 App 不得假设仍在内存。
- 系统资源不足时可以回收后台 App。
- 持续业务若需可靠存在，使用系统服务或持久化业务状态，而不是页面驻留。
- 页面恢复只做 best effort；重新启动被回收 App 时从 App Root 开始。
- 提供信息型、控制型、列表型和工具型页面指导。
- 使用一个最小 Runtime 样例验证契约。

## Out of Scope

- 同时实现四套 App 模板框架。
- 任意 App-to-App 导航历史。
- 后台驻留保证。
- 通用后台调度器或低内存杀手。
- 完整状态恢复框架。
- 新的 Runtime、Package Manager、App Manager 或 Shell abstraction。
- Pet、XiaoZhi、AI UI、MCP 或 ESP-Claw。

## Contract Gates

| 检查项 | PASS 条件 | 状态 |
|---|---|---|
| Canonical contract | Native、Runtime 与第三方指导使用相同术语和行为 | PASS（STATIC，dependency-gated） |
| Root / Detail | 两种执行模型都能验证 Root → Detail → Back → Root | PASS（HOST BUILD + STATIC，真机待验收） |
| Launch Source | Root Back 返回一个直接来源；失效时回 Watch Face | PASS（STATIC，真机待验收） |
| Home | 任意 App 页面 PWR 短按都回 Watch Face | PASS（STATIC，真机待验收） |
| Display State | 两种执行模型遵守相同息屏、唤醒和 fallback 规则 | PASS（STATIC，真机待验收） |
| Reclaim semantics | App 不依赖后台驻留；回收后重新启动进入 App Root | PASS（STATIC，真机待验收） |
| Gesture ownership | App 保留 Tap、Scroll、普通横滑、Long Press；系统保留 Edge Back 与 PWR | PASS（STATIC，真机待验收） |
| Guidance | 四类页面指导写入开发文档，但不建立模板框架 | PASS（[`../design/product/app-contract.md`](../design/product/app-contract.md)） |
| Minimal Runtime sample | 只实现验证契约所需的最小 Root / Detail 路径 | PASS（Toolkit build + staging，真机待验收） |
| Build | Native 与 Runtime 目标的 clean build/link/staging 成功 | PASS（2026-09-28，dependency-gated） |
| Static checks | JSON、package、脚本或项目既有检查全部通过 | PASS（Toolkit validation + JSON parse + `git diff --check`） |

## Hardware Acceptance

真机证据是 M8 PASS 的必要条件。M3 已通过；M8 仍须完成本规范自己的 Runtime 路径验证后才能 PASS。

### Fixed repetition counts

以下次数均为固定验收要求，且不超过 5 次。任何一次失败都必须记录，不能追加次数稀释失败。

| 执行模型 / 路径 | 次数 | PASS 条件 | 状态 |
|---|---:|---|---|
| Native Root → Detail → Back → Root → Back → Launch Source → PWR Home | 5 | 每轮导航和来源恢复均正确 | NOT TESTED |
| Runtime Root → Detail → Back → Root → Back → Launch Source → PWR Home | 5 | 每轮导航和来源恢复均正确 | NOT TESTED |
| Native background reclaim → relaunch | 5 | 从 App Root 启动，不恢复失效页面 | NOT TESTED |
| Runtime background reclaim → relaunch | 5 | 从 App Root 启动，不恢复失效页面 | NOT TESTED |

### Required one-pass checks

| 检查项 | PASS 条件 | 状态 |
|---|---|---|
| Native App Screen Off / Wake | 未回收时恢复页面；回收时降级 Watch Face | NOT TESTED |
| Runtime App Screen Off / Wake | 未回收时恢复页面；回收时降级 Watch Face | NOT TESTED |
| Native normal horizontal swipe | 不误触发 Edge Back | NOT TESTED |
| Runtime normal horizontal swipe | 不误触发 Edge Back | NOT TESTED |
| Invalid Launch Source | 两种执行模型都降级 Watch Face | NOT TESTED |
| Failure scan | 无 panic、watchdog、assert、deadlock、错误来源恢复或持续性资源下降 | NOT TESTED |

## Lifecycle / Heap Evidence

- 复用项目现有 lifecycle 与 heap 证据格式；不为 M8 建第二套框架。
- 回收可以通过明确、默认关闭的测试入口模拟，不要求实现完整低内存调度器。
- 每次回收必须证明旧页面和瞬时 Overlay 不再可恢复。
- 重新启动必须证明从 App Root 开始。
- Native 与 Runtime 的失败必须分别记录，不能互相替代。

## App Guidance Deliverable

开发指导至少应覆盖：

- 信息型：Big Value + Small Status + Optional Detail。
- 控制型：Status + Primary Controls。
- 列表型：Single Column List。
- 工具型：Single Task + Large Primary Action。
- 圆屏中部优先、单列列表、避免手机式 Bottom Navigation。
- 不依赖后台驻留，不阻塞 PWR Home，不占用 Edge Back。

这些内容是交互指导，不要求四套可执行模板。

## Evidence Rules

- 每次固定循环必须标识执行模型、attempt 编号、Launch Source 与最终目标。
- Runtime 路径必须使用真实 Runtime App，不能用 Native mock 替代。
- Preview、host 测试或串口状态打印不能替代物理显示、触摸和 PWR 观察。
- Runtime 路径未通过或任一必须项缺少证据时，M8 不得标记 `PASS`。

## Result

`NOT ENTERED`

M8 Native/Runtime 契约源码已按项目所有者授权提前开发，并通过 Toolkit、主机构建、staging 与静态检查；记录见 [`evidence/m7-m8/M7_M8_HOST_BUILD_2026-09-28.txt`](evidence/m7-m8/M7_M8_HOST_BUILD_2026-09-28.txt)。由于 M7 尚未 `PASS`，M8 仍保持 `NOT ENTERED`，所有真机和 lifecycle/heap 项保持 `NOT TESTED`。
