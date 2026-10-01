# 01 — 设备开发者模式与 USB 协议准入

**What to build:** 在设备上提供默认关闭、持久保存的开发者模式开关；正式固件中的 USB Test Adapter 只有开启后才接收版本化测试命令。

**Blocked by:** none

**Status:** resolved

- [x] 设备重启后开发者模式配置保持，关闭时任何测试刺激均不改变状态。
- [x] `hello` 能报告协议版本、镜像 identity 与支持能力；未知版本、命令明确拒绝，协议保留 `busy` 错误。刺激序列的并发拒绝由 [02 共享输入路径与只读快照](02-shared-input-and-snapshot.md) 验收。
- [x] USB 日志与测试帧可以区分；协议不暴露设置修改、安装或任意 App Action。
- [x] 记录 Native 与 Runtime 共享的产品层入口，不在 Brookesia managed component 中加入测试协议。

## Resolution

ESPocket 自有 Test Adapter 提供 USB Serial/JTAG 版本化帧，设备 Quick Settings 的开发者模式默认关闭并保存到 NVS。持久化写入由内部 RAM 栈的任务执行，避免 GUI 的 PSRAM 栈在 Flash cache 暂停时触发断言。正式固件只公布已实现的 `hello`；刺激序列和实际 `busy` 拒绝在 ticket 02 完成。构建与真机证据见 [2026-10-02 USB 准入记录](../records/2026-10-02-usb-gate.md)。
