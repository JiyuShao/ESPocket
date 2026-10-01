# 02 — 抽离并验证 GUI 资源

**What to build:** 将 Circular Shell 与 Hello Native 的内嵌 GUI JSON 移到各 Owner 的 `resources/gui.json`，使用 ESP-IDF `EMBED_TXTFILES` 嵌入，并以结构测试验证 action contract。

**Blocked by:** 01 — 统一 host checks 与测试位置。

**Status:** ready-for-agent

- [ ] Shell 与 Hello Native 各自只有一个权威 `resources/gui.json`。
- [ ] CMake 显式嵌入资源，C++ 不再保存大型 JSON 字符串常量。
- [ ] 测试比较 GUI 声明、订阅和 handler action 集合，并对缺失或多余 action 失败。
- [ ] 资源内容、manifest ID、用户可见行为和 Reference App 身份保持不变。
- [ ] Host checks 与固件 build 通过。
