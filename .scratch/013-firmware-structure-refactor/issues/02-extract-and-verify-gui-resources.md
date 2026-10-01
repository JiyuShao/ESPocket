# 02 — 抽离并验证 GUI 资源

**What to build:** 将 Circular Shell 与 Hello Native 的内嵌 GUI JSON 移到各 Owner 的 `resources/gui.json`，使用 ESP-IDF `EMBED_TXTFILES` 嵌入，并以结构测试验证 action contract。

**Blocked by:** 01 — 统一 host checks 与测试位置。

**Status:** resolved

- [x] Shell 与 Hello Native 各自只有一个权威 `resources/gui.json`。
- [x] CMake 显式嵌入资源，C++ 不再保存大型 JSON 字符串常量。
- [x] 测试比较 GUI 声明、订阅和 handler action 集合，并对缺失或多余 action 失败。
- [x] 资源内容、manifest ID、用户可见行为和 Reference App 身份保持不变。
- [x] Host checks 与固件 build 通过。

## Resolution

2026-10-02：GUI 资源抽离完成，原始 JSON 与 manifest 保持一致；action 声明／订阅／handler 检查及负例通过，完整固件构建通过。详见 [阶段记录](../records/2026-10-02-gui-resources.md)。
