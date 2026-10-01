# 02 — 默认 Back 与待决分发

**What to build:** 子页面统一可见 Back 与 Edge Back、App 级整体禁用开关，以及可由 App 暂缓确认的 Back 请求。

**Blocked by:** 01。

**Status:** ready-for-agent

- [ ] Root 不显示或响应 Back；子页面默认可见 Back 与 Edge Back 触发同一 `requestBack`。
- [ ] App 使用 ESPocket 标准 Back 控件时不出现双 Back；整体禁用默认入口的多级 App 必须自带可见 Back。
- [ ] 待决请求最多一个；重复 Back 不提交，超时取消并报告，迟到完成不改变新任务。
- [ ] PWR Home、App 停止或崩溃使待决 token 失效，不能被 App 阻塞。

## Comments

- 2026-10-02：已实施 Navigator Back 请求状态机、呈现模式声明和 Shell 默认可见 Back。主机接口测试与整机构建通过；真机确认 Native Detail 默认 Back、Edge Back、Root 无 Back 与 PWR Home。暂缓 Back 样例仍待后续接入，证据见 [M7 记录](../../../docs/milestones/m7/records/2026-10-02-default-back-prototype.md)。
