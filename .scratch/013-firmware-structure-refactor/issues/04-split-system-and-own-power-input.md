# 04 — 拆分 System 并收回 PWR Owner

**What to build:** 保持 `espocket::System` 的公开接口与状态 Owner，按启动装配、App lifecycle、导航、显示和 PWR 拆分实现，并由 System 直接消费 PowerKeyMonitor 事件。

**Blocked by:** 03 — 拆分 Circular Shell 并收敛 ShellHost。

**Status:** ready-for-agent

- [ ] `system.cpp` 保留启动与 composition root，App lifecycle、导航、显示和 PWR 分别进入职责明确的 `.cpp`。
- [ ] System 直接消费 PowerKeyMonitor 事件并执行 Home；Shell 不读取 PWR 计数。
- [ ] 内置 Native App 仍由 System 显式安装；可用私有 `install_builtin_apps()` 收拢顺序与错误处理。
- [ ] 不增加静态自注册、生成 registry、空 App Navigator 或新的公开 Interface。
- [ ] PWR、Home、wake、Display State、App lifecycle 与导航行为保持现有契约。
- [ ] Host checks、固件 build 通过，并完成一次集中的 PWR/ShellHost/navigation 真机 smoke。
