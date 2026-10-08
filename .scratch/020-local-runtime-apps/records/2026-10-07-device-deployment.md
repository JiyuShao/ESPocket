# 2026-10-07 — 本地 Runtime App 真机替换

## 部署输入与保留范围

用户确认直接部署并替换设备旧版，澄清 Reset 指硬件复位。本地 App 与产品镜像没有新增 Reset 按钮或 restart action。为避免覆盖设备已有的音频修复，部署输入包含较新的有界输出增益、WakeNet 模型引用释放、AFE WakeNet 装配和 fetcher priority 11；对应 Owner host fixtures 一起同步。

完整 32 MiB Flash 按 1 MiB 分段读取并校验，备份为 `/private/tmp/espocket-local-runtime-before.bin`，SHA256 `6df340899277bceb844db584fdf2aa4959a3020e91f4c0e952a5ecad57648257`。此前失败的读取未用于迁移。LittleFS 位于 `0xe60000`，长度 `0x11a0000`。

迁移镜像 `/private/tmp/espocket-local-runtime-staged.bin` SHA256 `2f42bd11b5fe515e740e1e837b053467dab8d4dcfcce9335db8c46ebbaa5426c`；保留全部 315 个既有文件，并复制旧聊天／计算器 data/files 到新身份。旧安装先保留供验证。原始摘要 inventory 保存在镜像同名 JSON，未打印个人配置内容。

只写入 App 与迁移 LittleFS，esptool 两区域写后 hash 校验通过；bootloader、分区表、NVS 和模型分区未写入。使用 USB 硬件 Reset，Core 成功验证并注册两个本地身份。

## 固件与检查

独立构建 `/private/tmp/espocket-local-runtime-20261007-v4` 最新镜像 identity `b7d076a00`，替代准备记录中的 `ad8326c75`。

- BIN SHA256 `3fa05a6af45f0d824adae9eec762e2910cdaf8d5d345a06e0ea5bdb57e0fc4c0`。
- ELF SHA256 `b7d076a0035f03ad982dcd589871d8378bfbfe4880d81583c3de3ea6b5f4cc14`。
- 模型构建产物 SHA256 `72447db11fd5bc683507ddd6727bea458473873019bf919858ed520a87429894`；本次不改写设备模型。
- 完整产品构建 PASS，最终 `python3 scripts/check.py` PASS：跨模块 160 项、1 项既有 skip，所有 Owner suites 通过。日志 `/private/tmp/espocket-local-runtime-deploy-host2.log`。
- 部署证据 `/private/tmp/espocket-local-runtime-deploy.json` 与 `.flash.log`、`.boot.log`；设备 hello identity 精确匹配。

## 真机结果

本地计算器实际启动 ID 为 `espocket.app.calculator`，触摸输入 `2 + 3 =`，截图结果为 `5`。Home 返回 Watch Face。

本地聊天实际启动 ID 为 `espocket.app.ai_chatbot`，显示 Internet ready、Activated、Connected 和 Ready to talk。设置及 Agent 选择页面可进入；两次边缘 Back 分别返回 settings 和 chat Root，canBack 从 true 回到 false，Home 返回 Watch Face。证据 `/private/tmp/local-proof.log` 与对应页面 PNG。

Store 截图注入 keepalive 触摸曾发生 Synthetic input tick timeout，未出现设备 panic；移除截图过程中的额外触摸后截图通过。串口重新打开会触发硬件复位；测试工具先收集启动日志并等待 Owner ready。Store 异步缓存加载期间可能重建界面，卸载前等待扫描完成并核对列表身份。

旧聊天通过 Store Installed 的 Uninstall 按钮交给 Core 卸载；随后硬件启动日志不再发现 `brookesia.general.ai_chatbot`，本地身份及其他安装仍注册。

旧计算器同样通过 Store 的 Uninstall 交给 Core，日志记录 App uninstalled id(6)，页面显示 Uninstalled Calculator，安装数从 11 变为 9。`/private/tmp/local-remove-calc.log` 与 `.png` 保存结果。硬件复位后的 `/private/tmp/local-final.log` 注册列表仅包含 2048、Clock、Flappy Bird、Music Player、NES、Weather、两个本地 App 与 Hello Runtime；两个旧身份均不存在。Native Store／Settings 保留。Launcher 截图每个名称只出现一次。

硬件复位后本地计算器删除一次错误输入再计算 `9 / 3 = 3`，截图 `/private/tmp/local-final-calculator-9divide3.png`。最终 Home 处于 Watch Face、foregroundAppId 为空、inputBusy 为 false，设备 identity 仍为 `b7d076a00`。

本地聊天复位后连接已有小智账号，无需重新激活；AFE 加载 `wn9s_nihaoxiaozhi`，真实音频通道打开。主机播放既有测试音频后，日志出现真实回复的 `ESP_GMF_ASMP_DEC` 输出缓冲扩容（需要 1920 bytes，由 1024 扩为 1920）；这条日志是正常解码器扩容，不能单独证明完整回复听感。截图捕获开始早于回复解码，因此仅显示 Chat ready。随后 Home 触发 server goodbye 与 audio channel closed，其他 App 可再次启动；本轮没有 panic 或栈溢出。

补充的重复语音测试被自动审批拒绝，理由是该测试音频会发送到已连接外部小智服务，需要针对具体音频／目的地的明确授权。已向用户询问；不绕过拒绝。完整回复内容、连续播放听感与实体 Reset 按键的人工手感未作为本轮自动验证结论；硬件 Reset 线复位、账号连接、回复解码和 Home 清理已有上述证据。

Markdown 与普通代码 diff 检查通过；diff 中 `.patch` 的四个空白告警均为 unified diff 的空白上下文行，保留补丁语法，不改写已构建输入。最终结果由 [02](../issues/02-device-replacement.md) 持有。
