# 2026-10-07 聊天与圆屏可读性修复

当前由 [16](../issues/16-chat-round-display-and-audio-usability.md) 持有；基线普通镜像 `bf237d3c7`。

## 基线

静置测试 `/private/tmp/espocket-chat-idle-baseline.py` 捕获音频通道开启后的自动息屏。测试窗口中出现用户／硬件唤醒与重开，最终 snapshot 为亮屏不能证明静置通过；针对窗口 `M6 display state: Off` 的断言失败。自动息屏没有直接 stop 普通 App，疑似会话停止需分开验证。

持久音量为 100，默认 Codec 初始化 75 后已加载实际值；调整默认值不能解决用户症状。AI Chatbot 0.2.1 使用 800×480 固定 GUI，当前缩为 329×197。默认字体复制 Montserrat 的行高，却挂载更高的 CJK fallback，存在多行重叠条件。

## 实现与验证

前台 Runtime AI Chatbot 的 timeout 由 System 跳过，Home 恢复普通 Shell 活动计时。默认字体合并真实 fallback 的 ascent／descent。Core 的产品 GUI 文档选择沿用原资源目录和 Controller，AI Chatbot 0.2.1 与 Calculator 0.3.0 使用嵌入圆屏布局，未知版本回退；LVGL viewport 的 App 背景扩展至全屏，随挂载／替换／卸载释放，不增加输入 Owner。

第一版普通候选 `cf01e98a5` 完整构建、17 组件精确补丁、114 产品／生成文件校验、160 项 host checks（1 项已有 skip）及 284 Markdown checks 通过。BIN SHA256 `72c413bfbb679550d6a78a472ed0a70d3d0b267535923be0ae6ae339755db0df`；ELF SHA256 `cf01e98a508931f5c42f85a87f1743f3a7a6e7eb86ad3f9e0f298a25f5a8c037`。App-only 更新 0x60000，其他分区与用户数据保留。启动 internal free/largest 为 27,159/18,432 bytes，PSRAM 为 6,287,428/6,160,384 bytes。

实际新界面已完成服务端识别／回复，多行中文截图 `/private/tmp/espocket-chat-round-immediate1-conversation.png` 的 20px 对话文本可读、无跨行覆盖，保留 Chat／Settings／Clear。首轮静置 95 秒的状态和完整日志都确认未自动息屏。其后的电脑问答被旧 harness 判为失败：该 harness 只观察首次 Decoder 输出缓冲扩容，日志却在静置中已捕获首轮音频分配；不能以此断言后续没有回复。后续改为固定声源加实际对话截图核验，错误的首次分配判定不作长期会话失败证据。

用户听过第一版后明确反馈仍太小。第一版的两倍增益按整个输出块的峰值限制，满幅瞬时峰会压低同块轻声。已先运行真实 callback 的瞬时峰／轻声回归并捕获失败，再改为四倍增益和连续峰值压缩：75% 满幅以上平滑压缩，输出始终在 int16 范围内，逐样本单调，轻声不受同块峰值抑制。Codec 的音量与 Mute 继续在其后生效，普通非 Decoder 播放维持原样。最终听感与候选真机验收仍待完成，不关闭工作票。

## 第二版候选

第二版普通候选 `3240aa233` 完整构建与 160 项 host checks（1 项已有 skip）通过；17 个组件精确补丁库存与 114 个产品／生成文件完全匹配。BIN SHA256 `334cca4aa64d1ddc1d39678dc82d06e25d3f6c84396d1418e2c349151c8d47ae`；ELF SHA256 `3240aa233434057e6a89391d27b4c3eafe84e560866cb1498fdbdca7063724d4`；patch-inputs SHA256 `918a382cc3b923abcafb3e4e1fb459ba282e6830a4339851b87bfdc5a4021900`。真实 callback 回归遍历全部 65,536 个 int16 样本，覆盖静音、单调、有界、瞬时峰／轻声、非 Decoder、非 16bit、默认增益和异常输入；这证明算法与真实输出接入，不代替扬声器听感验收。

第二版 App-only 刷入后真实回复通过，用户明确反馈声音够大但明显破音，音量验收仍未完成。新增实际 callback 的正弦波形保真回归捕获失败，说明逐样本压缩自身产生失真；第三版改为最高四倍、按整个音频块峰值限制的统一线性增益，保持波形比例和 int16 边界。这取舍允许满幅瞬时峰限制同块的轻声，不能同时以逐样本强增益和波形保真作为条件。保真与有界回归通过；第三版仍待真机听感。

第二版完整静置验收 `/private/tmp/espocket-chat-round-idle2` 在音频通道开启后 95 秒无触摸、无自动息屏。之后真实识别到“下。”并产生新的中文澄清回复，截图 `/private/tmp/espocket-chat-round-idle2-conversation.png` 已逐字检查，无空白方块与文字重叠；没有将短识别文本冒充完整声源问题。Home 关闭录音，Watch Face 静置 35 秒自动熄屏，未发生 panic、stream reset 或写音频失败。补丁补齐工作票关联后，第二版精确输入身份更新为 `b963337de11e39ef731966f0d4d4e8b73d1a1114494ea3ddcaf750ac10a64c93`，二进制未变。

计算器在第二版上用真实 Controller 完成 `12+34=46`、`789` 删除为 `78`、`60/5=12`、`5×2=10`、`00.4−0.2=0.2` 和 `50%=0.5`。`/private/tmp/espocket-chat-round-calculator2-*.png` 六张截图已检查，四角控制和底排按键完整位于圆内。结果区和按键均使用原包绑定与事件；UI 资源在第三版中没有变化。设备自动输入验收不能代替物理手指操作。

## 第三版候选

普通候选 `47fff80e5` 已完整构建，17 个组件与 114 个产品／生成文件精确匹配。BIN SHA256 `22efebc72fd246fc5044aee33dbded7e7c84b771b0f373578d7f59890989be10`；ELF SHA256 `47fff80e53824ac25f176c142f6d83ab567dd579e359b6f913ad076656b6a8a9`；patch-inputs SHA256 `507dfd3e17d9566657601d863798a5171eda5aa248b9fadb4ba5575ba6378455`。第三版仅改变 Decoder 增益 helper，产品配置仍为最高四倍；中文字体、常亮与圆屏文档保持与第二版相同。完整检查、真机听感及最终设备回归待完成。

第三版 160 项完整 host checks（1 项已有 skip）通过，App-only 0x60000 写入 hash 验证与启动身份通过。启动 internal free/largest 为 27,239/18,432 bytes，PSRAM 为 6,288,224/6,160,384 bytes。实际问答截图 `/private/tmp/espocket-chat-round-immediate3-conversation.png` 显示新的识别文本“那还正常吗？”和两段中文澄清回复；用户已明确确认“声音够用，破音明显改善”。这是实际扬声器听感证据，与最多四倍增益和保真正弦回归分开记录；没有声压计测量，不能给出设备 SPL 或宣称所有音源均无失真。

该问答退出后录音成功关闭，没有 panic、stop timeout 或 stream reset。截图传输期间观察到 AFE feed ringbuffer full，Home 收尾时 recorder FIFO read 返回 -2；二者不作正常无负载音频性能通过证据。最终导航和 App smoke 仍待完成。

第三版 `/private/tmp/espocket-chat-round-chat3` 和 `/private/tmp/espocket-chat-round-selection3` 验证设置、Agent 列表、重新选择当前 XiaoZhi、回到聊天、实际消息列表滚动、清空非空历史以及 Home。截图已检查：XiaoZhi 保持为当前 Agent，重开聊天取得新的服务端识别与澄清回复；滚动显示较早的气泡，Clear 后列表为空。没有以空列表上的滑动冒充消息滚动验收。

## 最大音量下调

用户在第三版确认总体改善后补充仍有轻微破音，并明确要求降低最大音量。第四版产品增益上限为 350%，输出峰值上限为满幅的 85%（27,851），相当于把满幅峰值再降低约 1.41 dB。这是数字 PCM 上限变化，不是扬声器声压测量；原音量 100 和 Mute 控制仍在后续 Codec 生效，不写用户 NVS 音量。HAL 配置新增峰值参数，默认 100% 保持上游普通行为，真实 callback 继续对整块使用相同线性增益。85% 峰值回归先在第三版失败，再通过第四版，正弦比例和所有 int16 值的有界回归继续通过；最终构建与真机验证待完成。

第四版普通候选 `94b3da4b0` 已完整构建，17 个组件与 114 个产品／生成文件精确匹配。BIN SHA256 `496be00ffa6538b7da9fd144c71c14819b2bb538ae58937823f6974ea0582bfd`；ELF SHA256 `94b3da4b0ae9e1d2243045557382f3b673bf5b78ed609b9d005e017c563c39e5`；patch-inputs SHA256 `f2584bf2e536b5a8c6d147390e11a2369dd61d20ed045f9b895d284457ca6c7f`。第三版八个非 Camera 原包 App 的启动、前台 snapshot、Home 与输入清理全部通过：2048、AI Chatbot、Calculator、Clock、Flappy Bird、Music Player、NES Emulator、Weather。该 smoke 证明基本生命周期，不能冒充各 App 的完整功能或物理手势验收。

第四版 160 项完整 host checks（1 项已有 skip）通过。App-only 写入 0x60000 的 hash 与启动身份通过，启动 internal free/largest 为 27,251/18,432 bytes，PSRAM 为 6,288,188/6,160,384 bytes。`/private/tmp/espocket-chat-round-listen4` 在音频通道开启后播放真实声源，50 秒试听期间不传输截图。该窗口中 AFE feed ringbuffer full、recorder FIFO read failure、stream reset 均为 0；Home 正常关闭录音。对照第三版截图窗口有 2 次 AFE feed full，故截图传输负载与正常试听分开验收。第四版听感、系统回归与最终合并仍待完成。

## 最终设备回归

第四版 `94b3da4b0` 的 App 57 步、navigation 34 步和 surfaces 22 步全部通过，报告位于 `/private/tmp/espocket-chat-round-flash4-device-suites/`。各套结束的 release 成功，snapshot 均为 Watch Face、无前台 App、无 pending Back、inputBusy=false。自动输入不等同于物理触摸／PWR GPIO 验收；圆屏截图与用户实际听感分别保存。

`/private/tmp/espocket-chat-round-background4` 在最终镜像上实际触发计算器数字 6，截图完整显示全部按键；结合前述运算和删除用例，19 个按键事件均已覆盖。Weather 实际显示深圳天气，外围使用其深蓝背景，仍采用安全内接 viewport；Home 截图恢复原表盘背景，无 App 背景残留。AI Chatbot 与 Calculator 已提供专门圆屏重排，其他 App 保留通用安全矩形，不能宣称所有第三方 App 的内容都已放大或重排。

第四版声源播放前没有 Decoder 输出扩容，播放后出现一次首次输出扩容，确认真实 Decoder 输出路径已执行；结合无截图的 50 秒窗口和正常 Home 收尾验证真实链路。第三版用户确认响度够用、破音改善后要求继续降低最大音量，第四版已按要求设置并刷入 350%／85% 的数字上限。第四版的听感问题已异步询问，尚未收到新的反馈；不宣称破音完全消失或所有音源无失真，后续听感反馈按新证据继续处理。

完整源码回归通过，最新 Markdown 检查 284 文件通过。暂存普通源码的 `git diff --cached --check` 通过；三个新增 unified patch 保留协议要求的单个空格空上下文行，逐行检查确认没有其他尾部空白。原包、账号和用户文件没有替换，只有 App 分区更新；本地合并和 worktree 清理由工作票最后一项收尾。
