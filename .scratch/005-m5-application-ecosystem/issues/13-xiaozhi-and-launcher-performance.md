# 13 — 小智配置与 Launcher 绘制

Sequence: 13

**Status:** resolved
**Blocked by:** 无；沿用固件写入、保留数据及完成后合并 main 的授权。
Origin: 2026-10-06 用户要求 AI Chatbot 运行小智或至少不再报错，并寻找 Launcher 滚动的其它方案。

## Scope

复现真实 AI 配置错误，使用 AgentManager 的真实选择与持久化入口切换 XiaoZhi；激活或硬件输入条件准确记录，不伪造云端或录音能力。修复妨碍配置的系统显示兼容；Agent 服务初始化与激活独立于会话录音初始化。Launcher 对照原列表测量绘制成本，按用户要求验证其它方案；实施每页四行、Release 提交的无动画分页列表，以减少连续重绘。保留 Core 投影与正常输入／导航，不降低看门狗。

## Acceptance Criteria

- [x] 原 AI 配置报错可复现；小智选择持久化，重开不再要求 Coze 配置；实际激活／连接状态如实记录；激活码播报中 Home 可停止并回收，不阻塞 Core。
- [x] AI 设置入口可见可用，App 原包不改写。
- [x] Launcher 同机操作对照有可量化结果，优化不误触发 App，安装状态投影保持正确。
- [x] host、Markdown、精确补丁构建和必要设备回归通过。
- [x] 完成后合并本地 main，清理任务 worktree，保留其他工作，不 push。

## Resolution

2026-10-07：代码与真机验收完成，修复提交 `d6b52e2` 已 fast-forward 合并本地 main，任务 worktree 已归档清理，本地仅保留 main，未 push。最终普通镜像 `0203fb1fc` 已取得小智激活码；播报中 Home 三轮及八 App 联合启动／Home、navigation／surfaces 通过，150 项跨模块 host tests 通过。Launcher 使用每页四行的 Release 翻页，warm 累计 draw 降低 55.25%。小智尚待账号绑定，Recorder／AFE 关闭，未宣称完整语音对话通过。证据见[小智／Launcher 验收记录](../records/2026-10-07-xiaozhi-launcher.md)。
