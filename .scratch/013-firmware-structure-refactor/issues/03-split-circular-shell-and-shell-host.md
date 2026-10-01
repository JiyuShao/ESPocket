# 03 — 拆分 Circular Shell 并收敛 ShellHost

**What to build:** 保持 Circular Shell 的公开类与状态 Owner，把生命周期、GUI document、Home gesture、keyboard 和状态刷新实现拆为局部文件，并用 `ShellHost` 参数对象收敛 System callback。

**Blocked by:** 02 — 抽离并验证 GUI 资源。

**Status:** resolved

- [x] `circular_shell.cpp` 保留 IApp 生命周期与装配，GUI document、Home gesture、keyboard 和状态刷新分别进入职责明确的 `.cpp`。
- [x] `ShellHost` 是值语义参数对象，只暴露产品语义查询与命令。
- [x] `ShellHost` 不暴露 GPIO、PWR 计数、LVGL 对象或 Service 实例，也不引入单实现虚基类。
- [x] 本 ticket 保留既有 PWR Home 转发行为，直到后续 System ticket 在同一提交中完成 Owner 切换；`ShellHost` 不新增底层 PWR 暴露。
- [x] Shell 的生命周期、导航、gesture、keyboard、状态和 GUI action 行为保持不变。
- [x] Host checks 与固件 build 通过。

## Resolution

2026-10-02：CircularShell 拆为 lifecycle/document/navigation/keyboard/status，实现共用 component 私有定义，公开类和状态 Owner 保持不变。ShellHost 收敛产品回调，不含底层 PWR、GPIO、LVGL 或 Service 实例；旧 PWR provider 暂留独立参数，下一阶段删除。Host checks、产品字符串比对与完整构建通过。见 [阶段记录](../records/2026-10-02-shell-split.md)。
