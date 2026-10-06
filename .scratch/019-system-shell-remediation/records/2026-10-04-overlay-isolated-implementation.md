# Overlay 与 Loading 隔离实施 — 2026-10-04

本记录只描述隔离副本。原 checkout、Store 工作与设备均未修改；未刷写、打开串口、重启或运行设备输入。03/04 不因此关闭，01/02/05 依赖状态也未改变。

## 输入身份与边界

输入为当时工作区全部维护源码/文档，包括未提交与未跟踪改动，绝非已提交 HEAD。baseline 位于 /private/tmp/espocket-019-overlay-zirm58y_/baseline，working 位于同目录 working。快照排除 .git、managed components、Board Manager 生成目录、build/dist、node_modules、虚拟环境与缓存。baseline 保持不变。依赖后续独立复制、按 Firmware README 验证 Settings/Boost/LVGL hash；生成目录只用于构建与文档检查，不进入交付 patch。

## 03 实施

- Core 仍持有请求身份、Dialog 队列和完成结果；只增加 Core 的只读请求身份查询补丁，不新增请求队列或通用 Overlay manager。
- Shell timer 先执行真实 System tick，再提交 GUI 选择。System 在执行已识别 PWR 时丢弃未提交的选择与手势；系统拥有的 Dialog 保留。已经交付 Core 的结果不做回滚声明。
- Dialog 隐藏键盘现有 subtree 并暂停输入，不重建 textarea；Dialog 更新保持这一规则。键盘回调检查 suspended/invalidated。恢复在 Owner tick 查询 Core 后才进行，查询发生在 LVGL 锁外；Core 已撤销但 GUI hide 仍被延后或调度失败的旧请求也不能恢复。下一 Core Dialog 可以接替已撤销的旧呈现，迟到 hide 只匹配旧身份。
- 默认 Back 在键盘期间可见，即使 App Root 不提供页面 Back。Edge Back 独立汇入相同键盘取消入口，不调用底层 Page Navigator；Dialog 优先阻止这两种入口。
- Display seam 在成功切换输入状态时暂停/恢复 Dialog 本地自动关闭计时；息屏期间收到更新，从更新定义的完整呈现时长开始。没有暂停 Core 操作、授权或生命周期。
- Core hide 先将呈现标记为失效，再等待 GUI 锁；失败时 callback 拒绝选择，Owner tick 重试删除。正常选择在成功删除 GUI 后才交付 Core，失败时保留草稿与待决结果。
- LVGL 对 Keyboard/Dialog/Back userdata 保留共享引用直到删除事件；停止时即使最先执行的 Loading 隐藏失败，也继续撤销所有输入、订阅和 binding；GUI 清理失败返回错误，保留已撤销状态并拒绝覆盖为新运行，不能假报成功并释放仍被 callback 引用的状态。这不是 02 的全量生命周期关闭证据，01/02 的错误处理必须整合此返回值。

行为回归直接编译实际 Dialog、键盘取消/隐藏/暂停/提交、Display seam、Loading 与 timer 首段；假 LVGL 只提供 sink 和可控制的锁/分配失败。覆盖 Owner mismatch、重叠/更新、默认取消入口、Root Edge Back、息屏/唤醒、系统提示保留、PWR 与待提交选择竞争、已提交计数不撤销、迟到结果、隐藏失败、userdata 延后释放。实际键盘创建/真实 LVGL 像素、物理 PWR、Core stop 同期完整设备路径仍需验收；这些测试不等同真机证据。

## 04 兼容增量与剩余工作

已接入锁定 Core 的 on_show_app_loading / on_hide_app_loading；Shell 提供圆屏底部英文反馈，无输入资格，位于 Keyboard/Dialog 后方。启动等待与 App 主动等待分别保留标记，启动返回只释放启动反馈，不吞掉 App 在 on_start 中主动保持的等待。停止/失败/卸载使对应反馈失效并重试 GUI 清理。主动显示拒绝非 Starting 或非前台 Running Owner；没有授予新权限或启动其他 App。

同步 System::launch_app → Core::start_app → Native on_start / Runtime start 仍使用 SystemApp 任务。Shell timer 的 System tick 也使用该任务。PowerKeyMonitor 的独立任务每 40 ms 采样，2 个 debounce samples，释放被识别为短按时只累加 pending counter；take_short_press 消费之后才进入 System Home。慢 on_start 能令输入识别后等待消费，随后同步 stop 也可能继续等待。因此新增反馈不能证明、也未解决 250 ms 上限。

固定 Super system.cpp 明确配置 Core Startup overlay，同时关闭 Core app launch transition；Super Launcher 在 shell_app_launcher.cpp 中使用自身 show_launch_overlay、图标动画/hold timer 后调用 start_app_after_launch。不能把关闭 Core transition 当成无需迁移这些路径。本次没有完成系统启动资源或 Super 自有 launch/icon 动画；04 保持未完成。

后续先与 01 的初始化/失败清理结果及 03 的集成对齐，再在真实 Core/App 执行边界拆开可取消的前台进入意图与不能假取消的已提交启动；需要真实 Owner 的取消/完成能力，不能只把 start_app 丢到另一条线程并并发改 registry/GUI。App 主动等待的具体操作期限与取消继续由 App Owner 定义。

## 验证

- Shell 组件回归通过（6 个测试，含实际 C++ 行为矩阵）；新增 Core 真实查询回归通过，覆盖 Owner mismatch、active/queued 区别、撤销、调度失败及同步 Runtime strand 不 repost。完整准备工具准确应用全部 Core patch 并校验 hash。
- Settings/Boost/LVGL host 依赖 hash 验证通过。
- 统一 python3 scripts/check.py 已执行，继承 Store Card replacement 夹具未声明 launcher_generation_ 的编译失败；从未改动的 baseline 另建验证副本重现相同错误。未修改 Store 夹具或产品源码来掩盖该失败。
- 首次统一检查另报告快照没有 .git、文档生成目录缺失。后续使用原 index 的只读 git ls-files（不是快照 HEAD）核查，并创建本地空生成目录用于文档目录链接检查；实际生成代码只位于独立构建工程。最终 Markdown 检查通过 256 文件，统一检查仅剩上述 Store 夹具失败，83 个跨模块 host tests 全部通过。
- 构建初次配置被沙箱 sysctl 限制；获自动审批后在独立目录重新执行。缺少板级生成配置的配置失败保留日志。后续临时辅助脚本曾错误写入换行字面量导致配置重试失败，已修正；不是产品源码故障。最终副本应用同一构建生成的 Board defaults，并再次强制 playback-only、Recorder/AFE/Video 关闭。最终完整构建通过，精确 registry lock、全部 production 补丁路径、playback-only 配置与字形检查通过。镜像位于 /private/tmp/espocket-019-overlay-build-zirm58y-final/firmware/build/espocket.bin，SHA256 为 48c14b33156ceeb38e4ccdcb27092bf00061a495a868db8ff055c5fd9d128ef1；实际 ELF/sdkconfig/patch-inputs 身份保存在隔离交付目录的 firmware-build-identity.json。该镜像未刷写，不代表当前设备身份。
- 没有新增真机、触摸、GPIO、视觉或 250 ms 测量证据。

## 集成顺序与冲突

先对比 coordinator 当前源码与本次 baseline，不对原 checkout 直接整目录覆盖。共享修改涉及 System loading overrides、launch_app 的启动反馈、生命周期 Loading 清理、PWR 未提交选择丢弃，以及 Shell timer、input/display seam 和 callback state。Store 的 system_navigation.cpp、system_lifecycle.cpp 与 circular_shell.cpp 已有有效基线改动，必须按 hunk 三方整合；不要撤销动态 Launcher、package policy 或 Card replacement 行为。Core manifest 追加 006-overlay-request-validity.patch（精确原始源码/hash、按顺序应用）；保留此前 Store 005 patch 字节与 metadata。System/Shell 新增 keyboard_valid、message_dialog_valid 回调以及 Core 的 has_app_keyboard_request / has_message_dialog_request 公共查询，调用不得持有 GUI 锁。与可靠性线合并 Core manifest 时保留两边独立补丁，不能覆盖整个 manifest。

与 01/02 协作时保留 Shell on_stop 的错误结果、未删除 GUI 的 userdata 引用和失效标记；重建 Running Instance 前必须真正清理旧 Overlay，不能因 on_start 重新分配状态便报告重复运行成功。最终统一检查中的 Store 夹具问题由其 Owner 整合当前变更后处理。

## 保留的设备门槛

03：键盘草稿 → Dialog → 更新/关闭 → 草稿恢复；键盘 default/左右 Edge Back 不 pop Page；PWR 同周期取消未提交选择、Home 后系统提示保留、Watch Face PWR 息屏；息屏更新、Owner hide/失效后唤醒不恢复旧请求；停止与 GUI 失败路径由真实 Core 资源事实支持。需保存镜像 identity、真实输入与视觉证据。

04：测试专用慢 Native/Runtime 启动、失败启动、输入竞争各三次；记录物理输入开始、PowerKeyMonitor 识别时间、System 消费时间、Watch Face 成功呈现时间，以识别至呈现为 250 ms 指标，另保留识别耗时。当前没有数值。未解决的同步启动/stop 边界不能通过缩短 Loading 动画绕过。
