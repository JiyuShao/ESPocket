# 03 — 接通覆盖与息屏生命周期及活动语义

**What to build:** 在现有 ESPocket System 中接通普通前台 App 的 Quick Settings/息屏 pause/resume，并让有效非触摸遥控输入参与既有闲置息屏策略。

**Blocked by:** [02 公共 seam 核查](02-source-and-gui-boundary.md)。

**Status:** ready-for-agent

- [ ] 复用 Core 生命周期与现有 Running Instance/前台恢复投影。Quick Settings 与息屏形成重叠暂停原因，第一次暂停才调用 on_pause，全部原因解除且同实例仍有效、仍有前台资格时才恢复。
- [ ] 覆盖→息屏→亮屏但仍覆盖、覆盖时 Home/停止/替换实例、重复事件、过期恢复与系统停止均不错误恢复；隐藏 Shell、Card 和持续 Service 保持各自 Owner。
- [ ] App 能通过真实 Owner 的公开事实区分覆盖和息屏，使遥控分别保留连接或释放并断开；不从 on_pause 名称猜测原因、不读取 Shell 私有字段、不另建生命周期 Manager。
- [ ] 有效遥控移动/点击/滚动沿现有 System/Shell 路径计为活动；旧实例、被覆盖或已息屏 App 的迟到活动不唤醒或延长屏幕时间。主动息屏立即生效，动画不算活动，不新增 App 自有息屏计时器。
- [ ] 暂停/恢复失败不报告虚假成功、不复活失效实例；连接操作不在生命周期回调里同步等待主机。Home 和 Quick Settings 保持可用。
- [ ] 有意义的 host 回归覆盖重叠原因、实例失效、重复/迟到事件及活动权限；兼容核查现有聊天、计算器、Settings 的 timer、键盘、对话框与异步完成路径，不因 Paused 丢失必须完成的 Owner 工作。
- [ ] 更新受影响的长期产品/开发契约，区分目标行为与证据；运行 firmware 与 Markdown 检查。实际设备行为归 [09](09-device-acceptance.md)。

## Comments

2026-10-09：用户接受复用 pause/resume。Core timer 仅向 Running App 分发，原作 LVGL timer 仍需 App 自行处理；不能只接通通知就认定所有工作已暂停。
