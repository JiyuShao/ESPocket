# 06 — 收敛 CI 并完成最终验证

**What to build:** 让 CI 与本地入口表达同一组 host checks，并用构建和既有验收结果证明结构迁移没有改变产品行为。

**Blocked by:** 05 — 收敛源码、构建与生成目录。

**Status:** ready-for-human

- [x] 文档 CI 收敛为统一 host-check workflow，不重复维护分叉的检查列表。
- [x] 完整 ESP-IDF build 保持独立 workflow 和独立报告。
- [x] Host checks、component tests、跨 component tests 与完整固件 build 全部通过。
- [x] 对照迁移前基线复核导航、App lifecycle、PWR、Display State、Native/Runtime contract 与 AI Native Exposure Decision。
- [ ] 记录 04 中真机 smoke 的结果；若结构阶段新增硬件影响，再执行对应验收。
- [x] 更新 `firmware/README.md` 的稳定目录规则、架构文档的最终 Owner/Interface，以及 `CONTEXT.md` 的 Reference App 术语。
- [x] `python3 scripts/docs/check.py` 通过。

## Comments

2026-10-02：CI、目录规则、Reference App 术语、最终 Owner/Interface 与自动验证完成；普通镜像已刷入，USB identity 已核对。04/06 只等待一次集中 smoke 的人工观察结果，不能以静态结果代替。详见 [最终验证记录](../records/2026-10-02-final-verification.md)。
