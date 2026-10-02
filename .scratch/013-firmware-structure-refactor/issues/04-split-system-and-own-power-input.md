# 04 — 拆分 System 并收回 PWR Owner

**What to build:** 保持 `espocket::System` 的公开接口与状态 Owner，按启动装配、App lifecycle、导航、显示和 PWR 拆分实现，并由 System 直接消费 PowerKeyMonitor 事件。

**Blocked by:** 03 — 拆分 Circular Shell 并收敛 ShellHost。

**Status:** resolved

- [x] `system.cpp` 保留启动与 composition root，App lifecycle、导航、显示和 PWR 分别进入职责明确的 `.cpp`。
- [x] System 直接消费 PowerKeyMonitor 事件并执行 Home；Shell 不读取 PWR 计数。
- [x] 内置 Native App 仍由 System 显式安装；可用私有 `install_builtin_apps()` 收拢顺序与错误处理。
- [x] 不增加静态自注册、生成 registry、空 App Navigator 或新的公开 Interface。
- [x] PWR、Home、wake、Display State、App lifecycle 与导航行为保持现有契约。
- [x] Host checks 与固件 build 通过。
- [x] 完成一次集中的 PWR/ShellHost/navigation 真机 smoke。

## Comments

2026-10-02：源码与构建已完成；System 在既有 App callback task 的通用 tick 中消费 PowerKeyMonitor 待决事件，Shell 不接触 PWR 计数或 Home 分发。真机 smoke 与 05/06 最终镜像集中执行，避免重复刷机和人工操作；05 的纯目录迁移先继续，04 的真机条件不据此勾选。见 [阶段记录](../records/2026-10-02-system-split.md)。

## Resolution

2026-10-02：用户在镜像 e8bbe74ff 上确认集中 smoke「全部正常」。Native Detail Edge Back、自动息屏唤醒保留 Detail、PWR Home/息屏/唤醒，以及 Quick Settings/Launcher 反向返回通过；只做本次集中路径，不重做旧十轮。见 [最终验证记录](../records/2026-10-02-final-verification.md)。
