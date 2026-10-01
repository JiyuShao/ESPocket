# 05 — 验证 remote package lifecycle

**What to build:** 一个兼容 signed package 完成 download、verification、install、launch、update、reboot discovery 与 uninstall，同时不破坏 Runtime isolation。

**Blocked by:** [03 package trust](03-enforce-core-package-trust.md)；[04 dynamic Launcher](04-project-dynamic-launcher-from-core.md)；[06 在线 Store 修复复验](06-adopt-online-store-stability-fix.md)；[07 Runtime keyboard isolation](07-isolate-runtime-keyboard-results.md)；[08 兼容签名包与发布路径](08-publish-compatible-signed-package.md)。

**Status:** needs-info

- [ ] 每个 lifecycle transition 都具有真机与串口 evidence。
- [ ] Native 与现有 Runtime App 保持稳定。
- [ ] 长时间 package lifecycle 中无 reboot、stale entry 或 permission leak。
