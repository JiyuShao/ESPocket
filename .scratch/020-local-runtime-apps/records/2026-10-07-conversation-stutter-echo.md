# 2026-10-07 — 连续对话卡顿与回复尾音重新输入

## 用户现象

本地聊天部署后，用户报告连续语音与文字聊天会卡。确认卡顿包含声音断续和页面卡顿；用户安静时，设备仍会将刚播出的最后一句当作新输入继续回答。不能将上一轮启动／导航／单次回复解码结果扩大为连续对话稳定性通过。

## 快速复现

运行 `python3 /private/tmp/espocket-echo-boundary-repro.py`，编译锁定 XiaoZhi `on_chat_event` 的 CHAT_SPEECH_STOPPED 实际任务体，以及 Agent Manager `start_audio_encoder` 的实际数据回调。环境只模拟半双工状态和麦克风帧，不发送网络数据，不操作设备。

复现：回复进行时麦克风帧被拦截；网络 speech stop 到达后，模拟仍在播放的尾音再次到达麦克风回调。结果 exit 1：

```text
HalfDuplex: speaker_tail_pending=true, speaking=false, microphone_tail_uploads=1
FAIL: reply tail can be uploaded as a new user input before playback drains
```

这是实际代码路径中的边界缺陷：远端事件立即清除 speaking，半双工上传门禁只检查 speaking。产品以异步 owned packet queue 播放，远端回复结束不保证实际声音已播完。该主机复现证明尾音可以经过上传门禁，未证明本次用户声音在真机中的声学相关性。

## 假设与可证伪检查

1. 播放尾音在恢复麦克风上传后被拾取：等待实际播放结束并清除旧采集帧后，无人说话的静音窗口不应产生新的 User 输入。
2. GUI 更新与音频任务争抢资源：同步记录消息更新、输入响应与 decoder queue 指标，应观察到卡顿时间窗口对应更新或阻塞。
3. 长时间队列／GUI 资源积压：连续对话中队列长度、内部 RAM 与 PSRAM 最大块、活跃 View／Timer／订阅应保持有界。

## 已核对与限制

`node /private/tmp/espocket-chat-history-probe.js firmware/runtime_apps/ai_chatbot/src/app/chatbot/lifecycle.js` 使用实际 appendHistory/renderMissingHistory/淘汰逻辑，模拟 GUI Owner，并追加 10,000 条合成消息。PASS：activeMessages 10、activeViews 10、peakViews 10、creates 10000、destroys 9990。排除 JS 列表自身无限增长，不覆盖真实 GUI 释放、文本排版开销或音频任务调度。

Audio Decoder 的 `is_stream_drained` 检查 source queue 和 queued_bytes；worker 在调用 HAL feed_data 前已弹出最后一块。stream_drained event 在 feed_data 返回后发布，而 HAL mixer 仍异步解码／播放。因此单独用当前 drain 接口恢复上传仍不足以排除扬声器尾音。修复需明确实际播放完成边界和采集积压处理，不能把队列空误当作无声。

后续用户已授权声学测试，修复与真机进展见[部署记录](2026-10-07-echo-reset-deployment.md)。卡顿根因仍在调查，票 03 保持未完成。
