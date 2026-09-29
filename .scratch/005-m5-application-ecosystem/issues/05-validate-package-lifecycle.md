# 05 — 验证 remote package lifecycle

**What to build:** 一个兼容 signed package 完成 download、verification、install、launch、update、reboot discovery 与 uninstall，同时不破坏 Runtime isolation。

**Blocked by:** 03 — 执行 package trust；04 — 投影 dynamic Launcher；官方 HTTP fix；Runtime keyboard owner isolation。

**Status:** needs-info

- [ ] 每个 lifecycle transition 都具有真机与串口 evidence。
- [ ] Native 与现有 Runtime App 保持稳定。
- [ ] 长时间 package lifecycle 中无 reboot、stale entry 或 permission leak。
