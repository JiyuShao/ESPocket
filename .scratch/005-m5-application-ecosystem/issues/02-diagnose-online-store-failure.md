# 02 — 诊断 online Store failure

**What to build:** 一份有源码支撑的诊断，区分 TLS allocation containment 与剩余 cancellation race。

**Blocked by:** 01 — 集成官方 Store。

**Status:** retrospective-resolved

- [x] 2/2 与 1/1 policy 分别记录。
- [x] 最终 crash 完成 TLS handshake 与 HTTP worker code symbolization。
- [x] 具有可提交上游的 draft 与脱敏 evidence。

## Resolution

1/1 policy 降低了 allocation pressure，但真机在 cancellation 时失败；无需继续执行不安全复现。
