# Shell 共享手势仲裁

- 日期：2026-10-02
- 范围：012/02 共享 Shell 输入路径的源码 slice。

## 实现与边界

把既有硬件 gesture lambda 的规则抽到实际 `shell_gesture.cpp`。Shell 的硬件订阅只映射事件类型、方向、边缘、Y 坐标与距离；内部 `handle_gesture` 与它共同调用同一仲裁。Shell 保有同一组原子输入状态，仲裁只排队 intent，实际 Surface/Back 的执行仍归原有 callback task。

Watch Face 四方向、周边页反向返回、App 普通横滑、Root/AppOwned Edge Back 禁用、Detail 两侧 Edge Back、Launcher 从顶部越过阈值后松手才返回等规则保留。没有通用手势 Factory、Card SDK、第二套导航状态或 Assistant 注册。

## 验证

- 17 项 host tests、M2 parser、Markdown 通过。
- 真实共享 C++ 模块用例覆盖四方向和 Card 边界、Quick Settings、93px 阈值、单次触摸不重复提交、息屏不产生活动、普通 App 滑动、两侧 Edge Back、Launcher 非顶部/顶部松手及不足阈值取消；确认仲裁没有直接修改 Surface。
- 第一轮 Xtensa 构建失败：目标 `int32_t` 是 long，与 int 字面量的 `std::max` 推导不一致。修为显式 `std::max<int32_t>`，未弱化编译选项；最终构建结果将在下文追加。
- 修复后的 ESP-IDF 6.0.1 完整构建/链接与镜像大小检查通过；App 大小 `0x5d2690`，分区剩余 43%。BIN SHA-256 `17304da449d85df8bd957d49271ded042d004cac76aebc8a7c6c101494e97df6`；ELF SHA-256 `7a9cc243af472fbb660a3686774a7471a94e7d96aebe0ef8c111ac1eb608b497`；日志 `/private/tmp/espocket-night-shared-gesture-final-build.log`。

## 后续

尚未接 USB 原始坐标序列、LVGL 注入、PWR 刺激或 release。取消/超时清理不能直接当正常 Release 交给 Launcher，否则越过阈值的失败序列可能提交 Home；后续须先取消 pending/pull 状态再清注入，并测试重复 release。硬件事件与合成事件的输入占用也要明确仲裁。以上不改变目前仅 hello/snapshot 的源码能力列表。

未刷写，没有新增物理或视觉通过项；013 与 M7/M8 的待验收路径继续保留。
