# 03 — 接通覆盖与息屏生命周期及活动语义

**What to build:** 在现有 ESPocket System 中接通普通前台 App 的 Quick Settings/息屏 pause/resume，并让有效非触摸遥控输入参与既有闲置息屏策略。

**Blocked by:** [02 公共 seam 核查](02-source-and-gui-boundary.md)。

**Status:** resolved

- [x] 复用 Core 生命周期与现有 Running Instance/前台恢复投影。Quick Settings 与息屏形成重叠暂停原因，第一次暂停才调用 on_pause，全部原因解除且同实例仍有效、仍有前台资格时才恢复。
- [x] 覆盖→息屏→亮屏但仍覆盖、覆盖时 Home/停止/替换实例、重复事件、过期恢复与系统停止均不错误恢复；隐藏 Shell、Card 和持续 Service 保持各自 Owner。
- [x] App 能通过真实 Owner 的公开事实区分覆盖和息屏，使遥控分别保留连接或释放并断开；不从 on_pause 名称猜测原因、不读取 Shell 私有字段、不另建生命周期 Manager。
- [x] 有效遥控移动/点击/滚动沿现有 System/Shell 路径计为活动；旧实例、被覆盖或已息屏 App 的迟到活动不唤醒或延长屏幕时间。主动息屏立即生效，动画不算活动，不新增 App 自有息屏计时器。
- [x] 暂停/恢复失败不报告虚假成功、不复活失效实例；连接操作不在生命周期回调里同步等待主机。Home 和 Quick Settings 保持可用。
- [x] 有意义的 host 回归覆盖重叠原因、实例失效、重复/迟到事件及活动权限；兼容核查现有聊天、计算器、Settings 的 timer、键盘、对话框与异步完成路径，不因 Paused 丢失必须完成的 Owner 工作。
- [x] 更新受影响的长期产品/开发契约，区分目标行为与证据；运行 firmware 与 Markdown 检查。实际设备行为归 [09](09-device-acceptance.md)。

## Comments

2026-10-09：用户接受复用 pause/resume。Core timer 仅向 Running App 分发，原作 LVGL timer 仍需 App 自行处理；不能只接通通知就认定所有工作已暂停。

## Resolution

2026-10-13：在真实 Core AppRecord 实现实例身份、覆盖/息屏/手动重叠原因、首次暂停与末次恢复、错误/异常保持 Paused；System 接通显示/Quick Settings 事实，前台恢复投影保留有效 Paused 实例。公开 Native 执行快照与 Runtime 可选 reason callback 区分覆盖和息屏；有效活动经实例/前台/input epoch 准入后写入 Shell 原 idle 路径，迟到活动不唤醒屏幕。

one-shot 在暂停到期后恢复分发一次，periodic 不补发；Runtime completion pump 显式保留，既有 Owner event、键盘/Dialog 身份和停止撤销保持。实际生产方法 host 回归、统一 firmware/Markdown 检查均通过，具体证据见 [本批记录](../records/2026-10-13-suspension-and-bubble-wrap.md)与 [开发契约](../../../docs/development/app-suspension-and-activity.md)。物理时序、无线/音效/触摸效果仍归 [09](09-device-acceptance.md)，本票不将离线结果认定为真机通过。
