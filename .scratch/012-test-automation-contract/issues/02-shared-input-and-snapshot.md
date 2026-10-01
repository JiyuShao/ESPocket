# 02 — 共享输入路径与只读快照

**What to build:** 合成触摸和 PWR 进入正式 Owner 的处理入口，快照读取 Home Space、显示、前台 App 与 Navigator Page/Back 状态。

**Blocked by:** [01 Developer Mode USB gate](01-developer-mode-usb-gate.md)；Page 字段依赖 [014/01 Navigator](../../014-app-navigation-card-contract/issues/01-page-declaration-navigator.md)。

**Status:** ready-for-agent

- [ ] 合成触摸覆盖 LVGL 点击与 Shell 手势仲裁，但不直接设置 Surface 或 App 页面栈。
- [x] 合成 PWR 调用 System 语义入口；报告明确它不覆盖 GPIO 链路。
- [x] 快照带单调序号，包含声明的 `pageId`、`canBack`、`backPending`，不包含私有页面参数。
- [ ] 完成、超时、断连、重启时释放触摸注入；重复 `release` 安全。
- [ ] 一条刺激序列尚未完成时，新的并发刺激返回 `busy`，不交错执行；主机测试覆盖这一拒绝路径。

## Comments

- 2026-10-02（夜间，PWR 排队）：USB 仅入队，System 输入任务消费并调用原有 PWR 语义入口；排队/执行占用、重复 release、期限取消及执行中取消的主机行为用例通过，固件构建通过。未刷写；触摸与跨输入共同占用仍开放，不提前关闭整票。详见 [PWR 证据](../records/2026-10-02-power-input.md)。

- 2026-10-02（夜间，共享仲裁）：Shell 硬件订阅与内部合成入口共同调用实际 `process_shell_gesture`，保留方向、阈值、App Edge Back、Launcher 顶部拉动/松手提交和 activity 语义。组件行为用例已通过；USB 轨迹和 LVGL 注入仍未实现，不提前勾选整项合成触摸条件。记录见 [共享仲裁证据](../records/2026-10-02-shared-shell-gesture.md)。

- 2026-10-02（夜间）：先完成只读 snapshot 的源码与组件 slice。System 读取实际 Shell Surface、显示与前台 token，Page 来自共同 Navigator 或明确的 Settings 例外；状态变化/未适配页面明确失败。协议仅为成功样本分配 seq，不序列化私有页面参数。新增主机用例覆盖模式准入、能力公布、实时 Owner 读取、失败不报 Root/成功序号及重叠调用 busy。源码未刷写，触摸/PWR、序列占用和 release 清理仍开放。证据见 [夜间记录](../../013-firmware-structure-refactor/records/2026-10-02-overnight-frontier.md)。
