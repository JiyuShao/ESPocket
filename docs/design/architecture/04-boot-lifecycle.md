# 启动与生命周期

这张图回答：设备从 app_main 到 Watch Face 的启动顺序是什么，Native 与 Runtime App 又如何进入统一生命周期？

## 系统启动

![ESPocket 启动生命周期](assets/boot-lifecycle.svg)

启动失败分为两类：

- Display、Touch、System Core 或 Shell 基础启动失败属于 fatal，init/start 返回错误并保留串口诊断。
- Time、Wi-Fi 与 Battery 状态不可用属于 recoverable，Shell 使用降级状态继续启动。

## App 启停与恢复

![ESPocket App 生命周期](assets/app-lifecycle.svg)

Native 和 Runtime App 共享 System Core 的 App 状态机与恢复 hook。Runtime backend 的加载细节不同，但产品层不维护第二套导航流程。

### AI Native capability 生命周期

App 进入 Running 后才能建立属于该 Running Instance 的 Semantic Registration。停止、崩溃、重启或回收会先使旧 Context、Action、Event 句柄和订阅失效，再完成实例清理；重新启动产生新的注册身份。需要跨 App 生命周期持续存在的能力由 Service 提供。

这一规则来自 [ADR-0008](../../adr/0008-app-ai-capabilities-follow-the-running-instance.md)，不要求 System Core 建立第二套 App 状态机。

## 源码锚点

- firmware/main/app_main.cpp
- firmware/components/espocket_system/src/system.cpp
- firmware/components/shell_circular/src/circular_shell.cpp
- firmware/managed_components/espressif__brookesia_system_core/src/app/manager.cpp
