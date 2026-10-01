# 06 — 收敛 CI 并完成最终验证

**What to build:** 让 CI 与本地入口表达同一组 host checks，并用构建和既有验收结果证明结构迁移没有改变产品行为。

**Blocked by:** 05 — 收敛源码、构建与生成目录。

**Status:** ready-for-agent

- [ ] 文档 CI 收敛为统一 host-check workflow，不重复维护分叉的检查列表。
- [ ] 完整 ESP-IDF build 保持独立 workflow 和独立报告。
- [ ] Host checks、component tests、跨 component tests 与完整固件 build 全部通过。
- [ ] 对照迁移前基线复核导航、App lifecycle、PWR、Display State、Native/Runtime contract 与 AI Native Exposure Decision。
- [ ] 记录 04 中真机 smoke 的结果；若结构阶段新增硬件影响，再执行对应验收。
- [ ] 更新 `firmware/README.md` 的稳定目录规则、架构文档的最终 Owner/Interface，以及 `CONTEXT.md` 的 Reference App 术语。
- [ ] `python3 scripts/docs/check.py` 通过。
