# 03 — 拆分 Circular Shell 并收敛 ShellHost

**What to build:** 保持 Circular Shell 的公开类与状态 Owner，把生命周期、GUI document、Home gesture、keyboard 和状态刷新实现拆为局部文件，并用 `ShellHost` 参数对象收敛 System callback。

**Blocked by:** 02 — 抽离并验证 GUI 资源。

**Status:** ready-for-agent

- [ ] `circular_shell.cpp` 保留 IApp 生命周期与装配，GUI document、Home gesture、keyboard 和状态刷新分别进入职责明确的 `.cpp`。
- [ ] `ShellHost` 是值语义参数对象，只暴露产品语义查询与命令。
- [ ] `ShellHost` 不暴露 GPIO、PWR 计数、LVGL 对象或 Service 实例，也不引入单实现虚基类。
- [ ] 本 ticket 保留既有 PWR Home 转发行为，直到后续 System ticket 在同一提交中完成 Owner 切换；`ShellHost` 不新增底层 PWR 暴露。
- [ ] Shell 的生命周期、导航、gesture、keyboard、状态和 GUI action 行为保持不变。
- [ ] Host checks 与固件 build 通过。
