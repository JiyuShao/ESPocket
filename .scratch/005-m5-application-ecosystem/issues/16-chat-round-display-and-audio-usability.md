# 16 — 聊天常亮、音量与圆屏可读性

**What to build:** 修复前台 AI Chatbot 的自动息屏，检查并改善真实回复音量，提供系统拥有的圆屏布局与正确字体行高，改善矩形 Runtime App 周围背景。

**Blocked by:** 无；正式麦克风／小智链路由 [15](15-enable-xiaozhi-voice-conversation.md) 完成。

**Status:** ready-for-agent

## Scope

用户报告聊天自动息屏后疑似停止、音量过小、文字重叠与矩形黑边。沿用 worktree 修复、真机控制、App-only 刷写、完成后本地提交与合并 main／清理授权，不 push。保留安装包、用户数据与账号，GUI 适配沿用原 Controller、事件与生命周期 Owner；上游修复仅在 hash 锁定的独立副本应用。

## Acceptance

- [x] 前台 AI Chatbot 静置至少 75 秒无自动息屏，之后真实问答仍能取得服务端识别／回复；Home 仍关闭录音，普通页面仍自动息屏。
- [x] 混合字体行高覆盖中文与英文 ascent／descent，实际中文多行截图无重叠。
- [x] AI Chatbot 使用全圆背景与可读字号，保留设置、Agent 选择、聊天、清空和真实事件路径；不改原安装资源。
- [x] 兼容 Runtime App 使用随 App 挂载／卸载的背景，四角控制仍可达，未知版本保留安全布局。
- [x] 明确实际播放链路音量限制，改善回复输出，保留真实音量／Mute 控制；记录客观增益与听感证据的区别。
- [x] 完整 host／Markdown checks、精确补丁和完整构建、App-only 烧录及 App／导航设备回归通过。
- [ ] 保存镜像身份、截图、测量和局限，合并本地 main 并清理任务 worktree／分支。

## Comments

基线在聊天音频通道已开启时捕获最后触摸后约 30 秒的 `M6 display state: Off`。持久音量已为 100，不能仅提高默认值。原 800×480 GUI 缩成 329×197，16sp 文字约 7px；英文主字体行高度量未覆盖中文 fallback。

证据与后续验证由[本轮记录](../records/2026-10-07-chat-round-usability.md)持有。
