# 真机交互自动化开发契约

Sequence: 012

Status: planned
Blocked by: none

## Problem Statement

仅靠人工触控和串口日志，Home Space、App Page、Back 与 PWR 的回归验证慢且难以重复。现有 Brookesia `inject_touch()` 可驱动 LVGL，却不能单独覆盖 Shell 读取硬件快照的手势路径。需要 ESPocket 自有测试入口驱动真实 Owner，并明确合成输入不能代替物理与视觉证据。

## Solution

在正式固件中加入受设备开发者模式控制的 USB Test Adapter。设备上开启并持久保存开发者模式，默认关闭；开启后命令直接可用。首版仅允许合成触摸、语义 PWR、只读快照和释放输入。Shell、Navigator、System 的状态从各自 Owner 读取，不维护第二套测试导航状态。

## User Stories

1. 作为开发者，我能在开启开发者模式后经 USB 重放触摸和 PWR 语义，并等到可观察页面状态稳定。
2. 作为测试者，我能读取 Home Space Surface、显示状态、前台 App 与声明过的 Page/Back 状态，而不读取 App 私有内容。
3. 作为验收负责人，我能明确区分合成输入、物理输入和视觉证据。

## Implementation Decisions

- Test Adapter 属于 ESPocket，借用 Brookesia Display、System Core 与 GUI 的公开能力，不修改上游组件以加入产品测试协议。
- 正式固件提供入口；开发者模式是设备本地持久配置，默认关闭。USB 是首版传输；Wi-Fi 留待后续。
- 命令语义限定为 `hello`、合成触摸/PWR、`snapshot`、`release`。确切线缆 schema 和语言类型在实现 ticket 中定版。
- 合成触摸的 Shell 手势进入与真实输入共用的处理入口；不得直接修改 Surface 或 Page 栈。
- 页面快照从 ESPocket Navigator 读取 `pageId`、`canBack`、`backPending`，不包含页面参数或整条栈。

## Testing Decisions

- 协议解析、开发者模式准入、并发拒绝、异常释放和序号等待需要主机或组件验证。
- 合成用例只能标记 `synthetic-input`；触摸芯片、PWR GPIO 和屏幕提示仍需各自真机证据。
- 设备未开启开发者模式时，所有测试刺激不得改变产品状态。

## Out of Scope

Wi-Fi 测试通道、任意 App Action、应用安装、设置修改、物理执行器和视觉自动识别。

## Tickets

- [01 — 设备开发者模式与 USB 协议准入](issues/01-developer-mode-usb-gate.md)
- [02 — 共享输入路径与只读快照](issues/02-shared-input-and-snapshot.md)
- [03 — 主机 Driver 与证据分类](issues/03-host-driver-evidence.md)

## Further Notes

- [开发者模式产品要求](../../docs/design/product/07-developer-mode-testing.md)
- [交互自动化架构](../../docs/design/architecture/08-interaction-test-seam.md)
- [测试开发协议](../../docs/development/interaction-test-protocol.md)
- [M7 验收](../../docs/milestones/m7/acceptance.md)
