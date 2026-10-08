# 2026-10-07 — 防回音与实体 Reset 恢复部署

用户已明确授权声学测试，并委托本会话托管另一会话的会话恢复工作。Reset 指实体硬件按钮；没有添加界面 Reset 按钮。“啊灰啊灰”仍是目标词，没有用现有“你好小智”替代验收。

## 构建与数据保留

独立增量构建从已验证 `b7d076a00` 输入更新 HAL 006、System 与 Navigation、本地 Chat 0.1.1。输入证明 `/private/tmp/espocket-echo-recovery-build-inputs.json`；构建成功，App 为 11,193,680 bytes，14 MiB 分区剩余 24%。镜像身份 `7094a19a4`，App SHA-256 `dab873733e5811a035529c6c24dd98dbbfcce14c0c628d4335a29bc281fb1e06`。

部署前重新备份当前 LittleFS 18,481,152 bytes，SHA-256 `2c6854745aa576ef836361dd1aec6b0e25029c51335215398268e04531e8ce24`。产品更新保留 299 个既有文件中的私有与其他 App 内容；只替换本地 App 代码并作废两个旧验证记录，由 Core 根据新固件的精确成员重新验证。编译 allowlist 的 35 个 immutable 成员与保存镜像完全匹配。只写 App 与保留镜像，NVS／模型／bootloader／分区表不写；两个写入区域 hash 校验通过。

更新工具新增显式 `--update-builtins`，拒绝动态安装 receipt；data/files/cache 已有内容优先于种子默认值。回归涵盖用户修改的种子文件、旧代码删除、验证记录失效、动态安装拒绝和备份保持。部署镜像与改进工具重新生成的镜像逐文件 inventory 相同（LittleFS 分配顺序可导致镜像总 hash 不同）。

## 设备恢复

`/private/tmp/reset-resume-after.json`：聊天前台硬件 Reset 线复位后 foreground 为 `espocket.app.ai_chatbot`、Page 为 `ai_chatbot_chat`；Home 后复位 foreground 为空、Surface 为 Watch Face。复现旧镜像失败与本镜像成功使用同一个 helper，helper 在 reboot 后重置序列号。

`/private/tmp/wake-reset-valid.log`：主动结束会话后，48,316 ms 音频通道关闭；现有“你好小智”在 55,806 ms 触发 AFE WakeStart，55,817 ms AgentManager WakeUp，55,953 ms 音频通道重开并产生回复。硬件 Reset 后再次恢复本地聊天，36,529 ms 音频通道打开，42,041 ms 收到回复 emoji。最后 Home 清理并返回表盘。该测试不验证“啊灰啊灰”系数或检测。

EN Reset 与冷上电在此板无法区分，二者均可恢复 opt-in 前台 App；Home 清除目标，软件／崩溃／看门狗重启不自动恢复。恢复重建 App Root，不保留旧运行实例。

## 回音与性能证据

播放防护在真实 PCM DAC 写入前后延长声学抑制；ADC 保持读取，抑制期间向 AFE 提供零帧。默认关闭，本产品设 250 ms 尾音保护。这是保守半双工抑制，不是 AEC，不将云端 speech stop 或 ingress queue 空当作播放结束。

真实声学输入先用 afinfo 验证非空，并临时将电脑音量由 13 提至 40，finally 恢复。首次沙箱 say 返回成功但产生零音频，本轮 `/private/tmp/echo-no-screenshot` 作废，不计语音成功。旧 baseline 仅有 decoder 输出，不能确认其为问题回复还是自动告别。

有效两轮 `/private/tmp/echo-valid`：两句固定输入得到两轮回复 emoji，截图前性能窗口没有额外回复 emoji、AFE 空缓冲、活动 FIFO 写入失败或崩溃。尚不能仅凭 emoji 计数完整证明没有额外 User STT，也不能据此宣称所有环境的回音已解决。

不截图时仍有 15 次 UDP 音频序号缺口，累计缺 19 包；页面更新单帧约 90–110 ms。连续卡顿没有关闭，下一步 WiFi 省电诊断 A/B；不能将正常 Home 关闭时 FIFO abort 与活动卡顿混为一谈。

## 检查

统一 host checks 全部通过（末轮 162 项，2 项因 littlefs 环境跳过，内置更新另用构建 littlefs-python 环境直接通过）。文档 markdown 检查通过。目标唤醒词的外部模型获取与连续卡顿仍由票 04／03 持有。

## WiFi 省电 A/B 与正式候选

先保存发布镜像 `7094a19a4`，只在隔离 HAL 副本的 WiFi start 后设置 `WIFI_PS_NONE`，生成临时身份 `54d431c2c`；只写 App，LittleFS 与所有配置保持。临时 `[DEBUG-echo-wifi]` 日志确认变量有效。相同两句非空输入、音量 40、节奏和截图前窗口，对比从 15 次缺口／19 包降到 0 次／0 包，两边均有两轮回复。样本是这次网络环境的有界对比，不能保证外部网络从不丢包。

临时源码已还原并重建，不进入仓库补丁。随后新增 HAL 007：WiFi Device 默认 false 的初始化前低延迟策略，由产品明确 opt-in。真实 backend 在 start 前设置省电，失败不会留下部分启动；接口已初始化时拒绝配置变更。`test_wifi_low_latency.py` 先在 006 Owner 运行失败，再在 007 通过默认行为、调用顺序、失败与配置冻结回归。正式候选 `c60a29d3b` 的完整输入证明为 `/private/tmp/espocket-echo-final-build-inputs.json`，没有临时 DEBUG 代码。关闭 modem sleep 增加联网功耗，耗电未量测。


## 最终设备状态与未通过路径

正式镜像 `c60a29d3b` 已部署，App SHA-256 `4fd7c657b22e0a4947993ba554319d426a25efa57860304aa347556d70828101`，设备 hello／表盘核对保存于 `/private/tmp/echo-final-deploy.json`。随后连续语音与滚动仍出现 `Synthetic input tick failed: timeout`，完整绘制单帧约 189 ms，原始日志 `/private/tmp/echo-final-voice.log`。因此 WiFi A/B 改善不能代表连续页面卡顿已解决，票 03 保持开放。
