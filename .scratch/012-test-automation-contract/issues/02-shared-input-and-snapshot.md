# 02 — 共享输入路径与只读快照

**What to build:** 合成触摸和 PWR 进入正式 Owner 的处理入口，快照读取 Home Space、显示、前台 App 与 Navigator Page/Back 状态。

**Blocked by:** [01 Developer Mode USB gate](01-developer-mode-usb-gate.md)；Page 字段依赖 [014/01 Navigator](../../014-app-navigation-card-contract/issues/01-page-declaration-navigator.md)。

**Status:** ready-for-agent

- [ ] 合成触摸覆盖 LVGL 点击与 Shell 手势仲裁，但不直接设置 Surface 或 App 页面栈。
- [ ] 合成 PWR 调用 System 语义入口；报告明确它不覆盖 GPIO 链路。
- [ ] 快照带单调序号，包含声明的 `pageId`、`canBack`、`backPending`，不包含私有页面参数。
- [ ] 完成、超时、断连、重启时释放触摸注入；重复 `release` 安全。
- [ ] 一条刺激序列尚未完成时，新的并发刺激返回 `busy`，不交错执行；主机测试覆盖这一拒绝路径。
