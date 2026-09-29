# 04 — 执行 user-goal authorization

**What to build:** Action 执行取已确认 User Intent 或 Scoped Grant 与 caller、risk、Owner 和 framework admission 的交集。

**Blocked by:** 03 — 增加本地 Assistant 入口。

**Status:** ready-for-agent

- [ ] App 或 Agent 文本本身永远不能授权 Action。
- [ ] Denied 与 high-impact path 明确。
- [ ] Post-submit 结果未知时不盲目重试。
