# 06 — 迁移六个游戏与玩具 Native App

**What to build:** 在 firmware/native_apps 下交付泡泡纸、打砖块、弹球、水池、太阳系和重力迷宫六个独立 Native App，保留原作玩法与圆屏视觉。

**Blocked by:** [10 自绘与多点接入](10-native-content-and-pointer-seam.md)； [02 源码/GUI/音效核查](02-source-and-gui-boundary.md)、[03 生命周期](03-system-lifecycle-and-activity.md)；使用 IMU 的对应 App 另依赖 [04](04-imu-capability.md)，不要求无传感器 App 等待硬件验收。

**Status:** ready-for-agent

- [ ] 六个独立 App 身份、Root、源码与资源通过既有 Native 注册及 Launcher 显示，用户可见文字中文化，关键内容位于圆屏可见可点区域；保留原作风格而不强制换成系统配色。
- [ ] 沿 02 锁定源码保留玩法/碰撞/物理逻辑，记录移植改动和素材归属。不带入原作 Launcher/Settings/Home handle/锁屏/分区，不新增全局 GameManager 或第二个导航栈。
- [ ] 复用现有 GUI 与 App 导航，系统保留顶边下拉 Quick Settings 与 PWR Home；系统手势的待决/取消输入不得变成游戏操作。
- [ ] on_pause 停止真实更新来源、动画及采样，保留同次状态；on_resume 自动继续并重置计时基准与触摸，不补算暂停时间；Home/on_stop 释放资源，重新打开从 Root 开始。
- [ ] 通过现有 Audio Service 播放短音效、遵守音量/静音，其他业务占用时跳过；不抢聊天音频或建立独立播放 Owner。
- [ ] IMU 错误时保留不依赖传感器的交互，受影响功能提示不可用并可重试/退出，不使用假数据；游戏动画不延长息屏时间。
- [ ] 不新增 App Card、后台驻留承诺或 AI 操作接口。共享代码仅限真实复用的纯玩法/适配逻辑，不抽象新的 App 框架。
- [ ] host/离线验证重点为暂停计时、状态恢复、输入取消、停止后回调和资源释放；运行 firmware 检查，六个 App 分别记录完成与未验证项。实际玩法验收归 [09](09-device-acceptance.md)。

## Comments

2026-10-09：原作多个游戏共用 app_games.c；按六个 App 拆分不意味着复制其全局状态或原作 Launcher。

2026-10-12：自绘与经过系统仲裁的多点接入由 [10](10-native-content-and-pointer-seam.md) 持有，属于本票实施前置。不得直接编入原作全局 LVGL/driver_data 路径来绕过该依赖。

## 分 App 状态

| App | 离线实现 | 真机 |
|---|---|---|
| 泡泡纸 | 独立身份、Root、自绘、受控多点、暂停/计时与可选短音效已实现；见 [本批记录](../records/2026-10-13-suspension-and-bubble-wrap.md) | 待 09 |
| 打砖块 | 独立触摸版已实现：五关、原碰撞/生命、自绘、受控拖动、暂停与短音效；见 [本批记录](../records/2026-10-13-brick-breaker-touch.md)。倾斜控制待 04 | 待 09 |
| 弹球 | 触摸版已实现：五个碰撞球、四个目标、双挡板、三颗球、自绘、受控双指、暂停与短音效；见 [本批记录](../records/2026-10-13-pinball-touch.md)。倾斜控制待 04 | 待 09 |
| 水池 | 触摸版已实现：380 粒子、小船浮力、RGB565 绘制、受控搅水和有界 App 工作线程；见 [本批记录](../records/2026-10-13-water-touch.md)。倾斜/摇晃待 04 | 待 09 |
| 太阳系 | 待实现 | 待 09 |
| 重力迷宫 | 待实现，另依赖 04 | 待 09 |

本票仍 ready-for-agent，不能以首个 App 通过离线验证关闭六个 App 的验收条件。
