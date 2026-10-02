# 01 — 定义 Semantic Registration 契约

**What to build:** 一套小型产品接口，表达 Owner identity、Context、Action、Event、Permission、Action Risk 与 lifecycle，不引入全局 state manager。

**Blocked by:** 无；用户于 2026-10-03 解除原产品顺序约束。

**Status:** resolved

- [x] 接口表达产品语义，不暴露任意 method。
- [x] Registration 与 invalidation lifetime 明确。
- [x] 设计为自身内部 seam 作出 Exposure Decision。

## Resolution

Owner-local public contract 与生命周期、授权交集主机测试完成。证据见 [2026-10-03 实现记录](../records/2026-10-03-semantic-brightness.md)与 [semantic interfaces](../../../firmware/components/espocket_semantics/README.md)。
