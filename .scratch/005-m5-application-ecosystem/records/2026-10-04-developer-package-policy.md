# 2026-10-04 — 开发者安装例外与 super 包兼容核查

用户接受开发者模式允许未签名包，普通模式仍要求发行签名。决策见 [ADR-0018](../../../docs/adr/0018-developer-mode-allows-unsigned-packages.md)，实施由 [09](../issues/09-allow-unsigned-developer-installation.md) 持有；尚未实现或刷入。关闭模式后已安装 App 的启动规则等待用户确认。

## 当前源码事实

Core 0.8.4 的 package.cpp supports_system 对 manifest systems 和设备 system_type 进行名称匹配；配置声明为空时有既有宽松逻辑。ESPocket 保持 system_type=espocket，Flappy Bird 0.3.0 只声明 super，因此原入口拒绝它。

对已校验官方 BPK 的源代码检查：启动 SystemCore、SystemGui、SystemTimer；GUI 用 CreateView、DestroyView、ExecuteBatch、GetViewFrame、SetBindings、SetViewSrc、StartViewAnimation、StopAnimation、SubscribeAction；Timer 用 StartDelayed、StartPeriodic、Stop。没有据此证明全部 API 或性能兼容。

资源使用 AppDefault 的 flappybird Screen Flow，单屏 initial=flappybird。没有 ESPocket navigation.json 页面声明。root.json 的 480x480 variant 仅在精确 480dp 方屏触发，466px 当前设备会使用默认资源。布局裁切、触摸、动画和生命周期均未验证。

## 建议方案与证据边界

设备可在 Core 同一兼容性判断中声明已测试的额外包兼容配置，保持自身 system_type=espocket，并保留原始包／manifest／artifact identity。Core manifest read、unpack、installation 与 reboot discovery 必须采用同一判断；Store 的本地包扫描也需要一致的准入结果。Root/Page 对接可由官方 App 兼容适配完成，不改游戏业务实现或维护第二份运行状态。

先验证指定 Flappy Bird artifact 的通用 API、资源、单 Root 适配、退出／重进，再决定是否接受该包；不把所有 super 包视为 ESPocket-compatible，不用改名或改包后保持原签名的方式制造兼容。当前只有设备侧兼容可行性结论，尚无准入策略实现、安装或真机运行证明。

## 后续共同理解确认

用户在 grill-with-docs 中确认：开发者模式允许所有声明 super 的 Runtime 包进入安装校验，不限定 artifact 白名单；不要求外部旧包接入 ESPocket 导航契约，不伪造页面快照。先前“单 Root 自动补充”和“仅指定包兼容”的建议被这一决定取代。Root/Screen 结构观察不能证明完整导航语义。

关闭开发模式后依赖任一例外的 App 保留安装、禁止启动，运行中实例停止回表盘；重新开启后重新准入。用户批准“开发者兼容安装”文案，安装界面不展示“页面导航未接入”；未签名额外说明发布者身份未验证。其他平台兼容能力按具体问题处理。政策已确认，源码、安装和真机运行仍未完成。
