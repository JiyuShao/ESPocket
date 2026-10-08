# 04 — 会话结束后的唤醒与实体 Reset 恢复

**What to build:** 用户授权本会话托管另一会话的恢复工作。会话结束后可继续对话；目标唤醒词为“啊灰啊灰”，Reset 为实体硬件按钮，不新增界面按钮。

**Blocked by:** “啊灰啊灰”的真实 WakeNet 系数尚不存在；须取得定制模型并验证 ESP-SR 2.4.4 兼容性、资源预算与真机识别。

**Status:** ready-for-agent

## Acceptance

- [x] 接手另一会话并停止串口／部署竞争；保持其研究结果。
- [x] Slept 正确显示等待唤醒；现有 Chat 操作通过 AgentManager WakeUp 恢复，主机回归通过。
- [x] Runtime 声明默认不恢复，聊天 opt-in；一次性检查点、Home 清理、崩溃不恢复主机回归通过。
- [x] 实体 Reset 线复位重新打开聊天并可对话；Home 后复位保持 Watch Face。
- [x] 会话结束后现有唤醒链路真机恢复通过。
- [ ] 取得“啊灰啊灰”真实模型并完成目标词验收，不能用“你好小智”替代。

## Evidence

定制模型来源、限制及官方申请渠道见[模型核查](../records/2026-10-07-ahui-wakenet-research.md)。EN Reset 与冷上电在当前板无法区分；恢复重新创建 App Root，而非保留旧实例或音频请求。

恢复真机证据见[部署记录](../records/2026-10-07-echo-reset-deployment.md)。

目标词对外询问已准备[草稿](../records/2026-10-07-ahui-model-request-draft.md)，未发送或接受协议。
