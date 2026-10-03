# App Interaction Contract

Sequence: 008

Status: resolved
Blocked by: 无；范围内 tickets 均完成。

## Problem Statement

Native navigation model 必须成为 Native、Runtime 与 third-party App 共用的稳定契约，并覆盖 reclaim、Root 无 Back 与待决 Back 行为。

## Solution

在同一产品契约下，使用真实 Native 与 Runtime App 验证 Root/Detail/Back、ESPocket Page 栈、Home、Screen Off、wake、reclaim 与 gesture ownership。

## User Stories

1. 作为 App author，我希望不同执行模型遵循同一交互契约。
2. 作为用户，我希望 Native 与 Runtime 的 Back/Home 行为一致。
3. 作为用户，我希望被回收 App 从 Root 重启，不恢复 stale page。
4. 作为 App，我希望普通 scroll、horizontal swipe 与 long press 得到保留。
5. 作为测试者，我希望 Native 与 Runtime 分别提供真机证据。

## Implementation Decisions

- 两种模型共享 System Core lifecycle 与产品导航语义。
- App 安装时声明 Root 与全部 Page 类型，ESPocket 保存唯一 Page 栈；Root 无 Back。
- App 可暂缓普通 Back，PWR Home 不受其阻塞。
- 需要可靠长期存在的工作归 Service 或持久化 business state。
- App 提供的 AI Native capability 遵循同一 Running Instance lifetime。

## Testing Decisions

- 具体前置见各 ticket：系统导航真机验收、Native/Runtime 新绑定与可控回收入口。既有 Runtime lifecycle 证据不能替代当前交互证据。
- Native 与 Runtime navigation/reclaim 路径各集中执行一次，按用户已要求减少重复操作；结果与失败保持独立记录。
- 使用真实 Runtime App，不使用 Native mock。

## Out of Scope

四套 template framework、任意 navigation history、后台常驻保证、low-memory killer，以及新的 Runtime 或 Shell 抽象。

## Tickets

- [01 — 既有 Native/Runtime 共享契约源码基线](issues/01-complete-shared-contract-source.md)
- [02 — 增加 Native 与 Runtime reclaim test seam](issues/02-add-app-reclaim-test-seams.md)
- [03 — 完成 App 交互真机验收](issues/03-run-app-contract-hardware-acceptance.md)

- [04 — 解决 Runtime 异步 GUI 栈溢出](issues/04-resolve-runtime-async-stack-overflow.md)

## Comments

- 2026-10-01：原问题与方案包括 `invalid-source` 行为、直接 Launch Source 验证，原实施决定为「App task 保存一个直接 Launch Source」。经 [ADR-0011](../../docs/adr/0011-app-root-has-no-back.md) 决策，Root 无 Back，ESPocket 保存 App Page 栈，首版不提供跨 App 返回；待决 Back 加入验收。上文为当前待实施范围，原方案保存在此作为决策历史。

## 当前结果与完成条件

四类页面指导及旧版 Runtime Toolkit/build/staging 基线已存在；这些结果不能证明新 Navigator、Root 无 Back 或待决 Back。新增语言绑定与开发 API 由 [014/04](../014-app-navigation-card-contract/issues/04-samples-api-finalization.md) 承接；本 Effort 完成 [02 回收入口](issues/02-add-app-reclaim-test-seams.md) 和 [03 真实 Native/Runtime 交互验收](issues/03-run-app-contract-hardware-acceptance.md)。两种执行模型分别保留证据，次数按 03 的单次集中验收规则。

- 2026-10-02：007/03 已完成；当前 apps 设备验收发现 RuntimeJsAsync 栈溢出，最小复现与诊断证据见[记录](records/2026-10-02-app-device-frontier.md)。03 等待 04 的上游能力，未关闭 M8，未推进依赖 M8 的 009。

- 2026-10-03：用户接受限定 Runtime 源码补丁方案；完整锁定构建、最小/完整 App 自动套件、两种独立 reclaim 与有限资源路径通过。已恢复普通 c8d56e5e2，原失败与缺失日志保留；008 仍等待物理/视觉条件，009 按依赖等待。见[补丁验证](records/2026-10-03-runtime-stack-patch-validation.md)和[晨间 frontier](records/2026-10-03-overnight-frontier.md)。

2026-10-03：008/03、04 的剩余物理条件完成，Effort resolved。原失败、有限资源范围和 Runtime 回收采集窗口差异保留，见[当前固件验收](records/2026-10-03-current-firmware-acceptance.md)。未验收的其他 Effort 不因本结论自动关闭。
