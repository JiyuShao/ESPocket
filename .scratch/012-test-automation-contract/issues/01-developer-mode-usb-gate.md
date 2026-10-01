# 01 — 设备开发者模式与 USB 协议准入

**What to build:** 在设备上提供默认关闭、持久保存的开发者模式开关；正式固件中的 USB Test Adapter 只有开启后才接收版本化测试命令。

**Blocked by:** none

**Status:** ready-for-agent

- [ ] 设备重启后开发者模式配置保持，关闭时任何测试刺激均不改变状态。
- [ ] `hello` 能报告协议版本、镜像 identity 与支持能力；未知版本、命令和并发刺激明确拒绝。
- [ ] USB 日志与测试帧可以区分；协议不暴露设置修改、安装或任意 App Action。
- [ ] 记录 Native 与 Runtime 共享的产品层入口，不在 Brookesia managed component 中加入测试协议。
