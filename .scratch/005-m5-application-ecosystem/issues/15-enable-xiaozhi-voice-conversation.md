# 15 — 完整接通小智语音对话

**What to build:** 将已验证的 ES7210 麦克风接入官方 Recorder／Opus／XiaoZhi DataFlow，修复实际启动与退出问题，让安装的 AI Chatbot 能完成真实语音对话。

**Blocked by:** 无；设备已获小智服务器激活认可，硬件验证由 [14](14-verify-official-microphone-capability.md) 完成。

**Status:** resolved

## Scope

2026-10-07 用户明确纠正“帮我完全修复”。授权正式产品启用与适配录音、编码、语音上传及回复播放，替代此前只验证或仅播放的当前实施范围。保留已有 App、用户文件、账号配置和已接受的播放／Launcher 修复；完成后本地提交、合并 main、清理任务 worktree，不 push。维护真实官方 Owner，原始 managed_components 不手工修改。

## Acceptance

- [x] 真机基线可重复捕获缺少 AudioEncoder0 导致的会话启动失败。
- [x] 默认产品构建装配正确的麦克风通道、格式、增益与官方音频服务，准确验证依赖和补丁输入。
- [x] 实际进入 AI Chatbot 能建立小智音频通道并开始监听，重新进入仍可用。
- [x] 真正从本机麦克风采集语音，经过编码／上传取得服务端识别和回复，设备实际播放回复；不使用注入 Capture 的假音频替代。
- [x] 英文界面内的动态中文识别和回复正常显示；默认字体保留原英文字形并提供中文缺字兜底。
- [x] 监听和回复播放期间 Home 退出、重开及相关 App 回归正常，录音不会在关闭 App 后继续上传。
- [x] 周期任务取消与再次排队竞态回归通过，联合 App 启动／退出不再触发已捕获的调度器空定时器 panic。
- [x] 延迟音频消费不再因借用缓冲完成等待而重置正常 Decoder 流；最终完整声学回复与退出通过。
- [x] 完整 host checks、Markdown、完整构建和最终普通镜像验证通过。
- [x] 记录身份、测量、失败、未验证项及实际使用方法，合并本地 main 并清理任务 worktree。

## Comments

基线实际命令为 `/private/tmp/espocket-xiaozhi-conversation-ready.py /private/tmp/espocket-xiaozhi-voice-baseline`，结果 `XiaoZhi conversation unavailable: Failed to get audio encoder interface`。已有双麦克风控制声源验证无需重做；本票继续真实官方服务和完整对话验收。

本轮可重复失败、内存预算与小智任务退出修正由[语音修复记录](../records/2026-10-07-xiaozhi-voice-conversation.md)持有；只有完整真机对话与退出证据到位后关闭。

用户已确认真实语音正常，并报告对话文字显示空白方块；字体修复及真机文字验收同属本票。

最终普通镜像 `bf237d3c7` 的真实问答／中文截图、累计三次实际回复中的 Home／重进、八个非 Camera 原包和 113 步 Native／Runtime 系统回归通过，156 项 host checks（1 项已有 skip）与精确构建／App-only 校验通过。两次电脑播音未取得回复单独记为未响应，未冒充连续三轮成功或识别率证明；具体条件和局限保留在同一记录。合并与清理结果见下。

## Resolution

正式产品接通官方 Recorder／AFE／Opus／XiaoZhi；准确匹配动态任务释放、拒绝无效模型头并将 TLS 动态内存移到 PSRAM。默认字体保留 Montserrat 并提供共享有界中文 fallback；真实 Owner 内修复 timer 取消／再次排队竞态及逐包借用完成超时误重置音频流。

实现与验收提交 `5850a8b` 已快进合并本地 main。任务 worktree 已归档并移除 checkout；实际 Git worktree list 仅主仓库，本地 branch list 仅 main，没有 push。普通镜像 `bf237d3c7` 留在设备，最后为 Watch Face，录音已停止。使用方法与所有失败／未响应轮次保留在[记录](../records/2026-10-07-xiaozhi-voice-conversation.md)。
