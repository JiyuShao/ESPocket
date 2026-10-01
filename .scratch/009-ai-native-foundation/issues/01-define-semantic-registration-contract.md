# 01 — 定义 Semantic Registration 契约

**What to build:** 一套小型产品接口，表达 Owner identity、Context、Action、Event、Permission、Action Risk 与 lifecycle，不引入全局 state manager。

**Blocked by:** [008/03 App 交互真机验收](../../008-m8-app-contract/issues/03-run-app-contract-hardware-acceptance.md)。

**Status:** ready-for-agent

- [ ] 接口表达产品语义，不暴露任意 method。
- [ ] Registration 与 invalidation lifetime 明确。
- [ ] 设计为自身内部 seam 作出 Exposure Decision。
