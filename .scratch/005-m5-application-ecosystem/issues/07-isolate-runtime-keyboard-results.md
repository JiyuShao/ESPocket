# 07 — 隔离 Runtime keyboard result 与失败停止清理

**What to build:** 使用官方 Core seam，保证 keyboard result 只交付给请求 Owner，或在 Runtime stop failure 时无条件完成清理，关闭已确认的跨 App 结果泄露路径。

**Blocked by:** owner-scoped result 与 queued callback 的真实回归及设备门槛；用户已授权维护锁定版 Core 补丁。

**Status:** ready-for-agent

- [ ] 核对并采用覆盖 `KeyboardClosed.Text` 广播与 failed-stop 残留订阅的官方修复，记录版本与源码边界。
- [ ] 使用真实 Runtime App 验证其他 App 的 keyboard result 无法被读取；覆盖正常停止和故意失败的 `on_stop`。
- [ ] 失败停止后订阅、callback 和 Running Instance 资源按契约失效，不污染后续 App。
- [ ] 记录 clean build、镜像 identity、真机与串口结果；原 fail-closed keyboard latch 只有在对应保护被证明后才能调整。

## 当前 containment

锁定版 Core 的缺口与“Runtime stop failure 后永久禁用 keyboard，直至重启”的产品 containment 见 [Store 报告](../records/2026-09-28-acceptance-report.md#runtime-keyboard-event-isolation)。已有 containment 不证明上游 isolation 已完成。

## 当前实施

[2026-10-03 failed-stop 回归](../records/2026-10-03-core-failed-stop.md)已证明并修复生命周期失败跳过 Runtime cleanup 的控制流。补丁已接入独立 production patch-set 构建并通过普通 App 自动验收；恶意 Runtime 订阅与故意失败退出的完整隔离门槛仍待完成。
