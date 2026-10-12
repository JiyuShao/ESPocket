# 2026-10-12 — 来源锁定与实际接入边界

## 授权与输入

用户要求在没有真机时完成可离线可靠性工作后继续 028，按此前已经接受的七个 Native App 方案推进；不再将“完整共同理解最后确认”作为重复许可门槛。物理验收仍待设备。

The-Badge 完整 commit 为 `76172dfaf0fa0ffedee91a61da3261afdde56ce3`，通过公开 Git 仓库获取。28 个选定源码/素材文件以原字节保存在 [迁移输入](../../../firmware/native_apps/badge/README.md)，总计 5,305,569 bytes；`upstream.lock.json` 固定每项 SHA-256 和大小。当前输入不编译、不注册 Launcher 应用；未把原作整个启动工程迁入 ESPocket。完整克隆暂存 `/private/tmp/espocket-028-the-badge-20261012`，长期事实以版本化来源锁为准。

许可证：项目 MIT，保留 LICENSE 原文；NOTICE 逐项给出素材与 NASA 图像来源。官方 GAP 示例文件头为 Unlicense OR CC0-1.0，保持原样。NASA 来源是上游 NOTICE 的归属声明，本轮未重新独立核查每张原图 caption；保留来源而不声称 NASA 背书。未引入新字体文件，中文使用产品已有字体。

上游没有提交 dependencies.lock；`waveshare/qmi8658: ^2.0.0` 不是已解析的精确版本，不能据此升级生产依赖。已读取[官方 2.0.0 组件页](https://components.espressif.com/components/waveshare/qmi8658/versions/2.0.0/readme)，其指向 Waveshare commit `9daffb7168b3c093a330da700988a22092294eef` 的 `sensor/qmi8658`。该目录 idf_component.yml 声明 2.0.0 / IDF >=5.3.2，license.txt 为 Apache-2.0；实际实现提供 `read_accel`（由配置选择 mg 或 m/s²）、`read_gyro`（dps 或 rad/s），头文件额外声明的四个单位专用读取函数没有对应定义。移植必须明确设置单位并使用实际存在函数；I2C 地址、安装轴向和稳定窗口仍需真机。

## 七个 App 的实际依赖

| 目标 | 锁定来源 | 必须适配的依赖 |
|---|---|---|
| 泡泡纸 | app_games.c 的 pop_start/pop_step/pop_cb | App 独占状态、LVGL 对象/timer、短音效；不用原 Games 菜单和 Launcher handle |
| 打砖块 | app_games.c 的 brk_start/brk_phys/brk_touch | 自绘球/砖/挡板、触摸与可选加速度、定步计时、音效；暂停不积累 dt |
| 弹球 | app_games.c 的 pb_start/pb_phys/pb_touch | 同上，独立 flipper/score 状态；不能与打砖块共享同一静态游戏实例 |
| 重力迷宫 | app_games.c 的 maze_start/maze_step/maze_touch | IMU 与触摸倾斜分别标明来源；原 s_fake_gx/gy 不能伪装硬件样本 |
| 水池 | app_water.c / water.h | 粒子模拟、PSRAM buffers、独立物理任务/信号量、LVGL draw/canvas、IMU；phys_wait 超时未确认任务退出时不得释放共享 buffer |
| 太阳系 | orb.c/h 与 app_games.c 的 orb_menu | 四种天体选择、纹理/canvas、LVGL timer、拖动；Root/选择页声明归 App Page，原 back 按钮不能替代系统导航 |
| 蓝牙遥控 | app_mouse.c / host_pick.c / hid_mouse.c / esp_hid_gap.c | 两种模式、原多点触摸、gyro、GATT HID、bond/host 管理、灵敏度持久化；移除隐藏清配对、原全局 top layer/keypad、keep_awake 与无线切换策略 |

app_games.c 的共享静态 globals 不支持多个独立 App 同时保留实例。迁移实现需要分离实际状态与生命周期，不能仅把同一 `enter/leave` 函数注册成六个 ID。水池有独立 FreeRTOS 物理任务；Core Paused 不会替 App 停它。原水池/游戏有传感器缺失的模拟输入路径，必须转为已确认的明确降级交互。

## 公共接口核查

| 能力 | 当前事实 | 实施 Owner 与下一步 |
|---|---|---|
| 自绘 GUI | AppGuiRuntime 只按 App document 操作公共 View；View 不公开 LVGL 对象；CanvasCommand 只有基本矩形字段，无动态 RGBA/原生子树 API | 在 GUI Runtime/LVGL Owner 内增加有界挂载：仅对调用 App 的已加载 container，在 GUI 调度与 thread guard 内创建子树，父节点卸载前撤销回调并清理；Core 仅转发 App 身份，不接管绘制。不能暴露全局 screen 或让 App 取私有 backend record |
| 两指输入 | HAL TouchIface 有 max_points/read_points；Display/LVGL 的现有手势管线消费输入，App 没有经过仲裁的多点快照接口 | 复用 Display::get_touch_snapshot 的真实多点采样和现有 MultiTouchPointerManager，再向 App 提供取消/有效性受控的快照，避免 App 再读硬件或照抄 adapter driver_data magic；顶部手势取消后不得产生 HID/游戏操作 |
| IMU | 当前 HAL interfaces 和该板注册无 Motion 能力；官方驱动存在 | 04 负责 HAL/Board 注册及单位、采样使用期限、错误与迟到样本；App 不初始化 BSP/I2C |
| BLE HID | 现有 PeripheralIface 配置只支持 write/write_without_response/notify，没有 read value/descriptor/bond 安全接口；HAL adaptor 选择 NimBLE | 05 在同一 BLE Owner 补足 HID report/read/descriptor 与配对资源。原 ESP-IDF esp_hidd/GAP 的 Bluedroid 全局栈不能和现有 NimBLE 并启；不能直接把 port_hid_* 拷入 App |
| 短音效 | Audio Service 已有 Source/Stream/PlayUrl 资源仲裁和系统音量/静音 | 06 通过真实 Audio Owner 申请低优先级短 PCM，其他业务占用跳过；不复用原作 codec/tone 独占实现，不抢占语音 |
| 暂停/活动 | Core pause/resume 已有，App timer 只向 Running 分发；System 当前覆盖/息屏不触发 pause；App 无公开暂停原因/有效非触摸活动入口 | 03 用现有实例身份处理重叠原因与活动资格，App 自己停 LVGL timer、物理 worker、IMU/HID。兼容既有聊天/键盘/异步完成路径 |

## 尚未完成

公开自绘与多点输入 API 的实现和失效回归仍未完成，不把表中的目标当现成接口。02 已完成来源与方案核查，具体声明与实现由 10 持有，随后 03–07 执行；来源锁和官方驱动核查已完成，不再重复确认 App 数量、玩法或产品行为。未访问设备、未启 BLE、未配对、未发送 HID、未刷机，未声称任何新 App 可运行。

## 补充源码约束

官方驱动的初始化在 bus_add_device 成功后的 WHO_AM_I/配置失败分支没有移除 I2C device；HAL 接入必须持有获得/释放关系，不能把官方 init 返回失败当作没有资源。本轮未修改该驱动。现有 BLE backend 明确设置 sm_bonding=0，配对记忆也不是已有功能。来源锁另保存官方驱动 5 个关键文件的 SHA-256，未加入生产 dependencies.lock。

## 选定的最小自绘接入方案（待实现）

保留每个 Native App 的 JSON Root/container 与既有 Screen Flow/App Page；自绘对象只挂在这个 App 的 container 下，SystemTop 不变。普通圆形控件可继续使用既有声明式 View；水池、天体与需要保留原作绘制的页面使用下面的受控扩展，不把所有 App 改造成新 GUI 框架。

目标 API 为 `AppGuiRuntime::mount_native_content(path, shared_ptr<gui::NativeContent>)`、`invoke_native_content(token, callback)`、`unmount_native_content(token)`。返回的 token 由 GUI Owner 分配，绑定 document/node/本次挂载身份，旧 token 不能访问新挂载；Core 只验证调用 App 的 document 并转发，不能让调用者指定其他 App 的 document 或全局 screen。

`gui::NativeContent` 只是 backend 扩展对象的寿命边界；实际 LVGL 接入类型位于 `gui::lvgl`，以受 GUI thread guard 保护的 attach/detach 回调提供所属父对象。App 不查找 backend 私有 Record、不保存 Runtime 的私有 handle，不加载全局 screen。GUI Owner 在节点 destroy/unload 前先撤销 token、断开事件并调用 detach，随后释放子树；detach 负责停止原作 LVGL timer/动画并断开回调，失败不能宣称已全部释放。App 的 pause/resume 通过 invoke 进入同一 GUI 调度域操作自身 timer，不能在 System Owner 上同步等待物理 worker。

多点输入沿已有 Display TouchSnapshot 与 MultiTouchPointerManager，给本次挂载提供有效 sequence、points 和取消事实。系统手势消费、覆盖、息屏或 token 失效后禁止投递；所有 App 手势使用这条管线，不读 HAL/adapter driver_data。先覆盖顶部序列取消、触摸点数变化、旧 token、挂载失败与 unload 竞态，再接入应用。

这是待实施的公开 seam 设计，当前源码尚无这些声明。实施单元见 [10](../issues/10-native-content-and-pointer-seam.md)；其失败回归和完整构建独立完成后，06/07 才能关闭自绘接入条件。现有聊天/计算器/Settings 不使用该扩展，其文档、binding 和 Screen Flow 继续走原路径。
