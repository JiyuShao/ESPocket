# 2026-10-08 — Shell Overlay 呈现离线整改

## 改动与归属

真实 CircularShell module 的呈现仲裁、Owner timer、Quick Settings transition、Keyboard／Dialog 结果交付、GUI 清理重试与实际 on_stop 集中到 `shell_overlay.cpp`；共享声明与呈现状态位于私有 `shell_overlay_internal.hpp`。没有新增 class、请求队列、状态 registry 或 lifecycle Owner。

Keyboard／Dialog 继续持有各自绘制 implementation，新对象先隐藏，再由同一呈现规则决定输入可见性。Dialog 不再直接调用键盘 suspend，公开 `suspend_keyboard_input` 已删除。GUI/state 锁外查询 Core 有效性和显示状态，并交付结果；协调未完成时不交付选择，稳定呈现不每 50ms 重取 GUI 锁。

Core 继续持有 request identity、有效性与最终结果裁决；Shell 原有 Dialog 自动关闭呈现计时不迁移。QS 覆盖继续计时，息屏暂停该呈现计时；此处澄清前置讨论中把全部“期限”归 Core 的过宽表述。PWR 仍由 System 处理，先丢弃未交付选择。

## 测试与构建

- `python3 scripts/check.py` 通过：217 tests，2 skipped；日志 `/private/tmp/overlay-presentation-check.log`。
- 随后将原有实际 on_stop 也纳入完整呈现 translation unit，并更新相关专项入口；最终 `shell_circular` 13 项回归通过，日志 `/private/tmp/overlay-presentation-shell-final.log`。最终 source 的改动仅有排版和移除重复默认宏，不改变已验证行为。
- 两项旧 Overlay 源码抽取测试由 `test_overlay_presentation.py` 替换。新测试编译真实 class 声明、私有状态、完整呈现、实际 Owner timer/on_stop、绘制与 Gesture implementation，经现有 public interface 操作，观察 GUI sink 和 Host 结果；不重声明 Shell、不抽取生产源码、不读取私有状态。
- 连续场景覆盖：QS→Dialog 过期→有效键盘原草稿恢复；有效 Dialog 优先恢复；待交付选择被覆盖后超时；App 请求撤销；PWR 丢弃未提交结果；GUI lock/删除失败重试且只交付一次；新旧请求隔离；渲染更新失败保留原对象；息屏期间更新计时；QS source/flow 失败；Loading 双用途清理；稳定键盘不反复取 GUI 锁；实际停止失败撤销旧回调、第二次 stop 完成清理。
- 首次 host adapter 编译暴露事件常量顺序及多 translation unit 的 inline 声明问题，已修复夹具。新 README 首次文档检查缺少入链，已从 Firmware README 链接。
- `python3 scripts/docs/check.py --markdown` 与 `git diff --check` 通过。
- ESP-IDF 6.0.1 隔离产品构建及最终源码增量链接通过，日志 `/private/tmp/overlay-presentation-final-build.log`。编译 Shell 源码、头文件、资源和 CMake 与 checkout 逐文件一致。原 managed Core／GUI source inventory 未改，隔离 patched inventory 精确匹配维护 manifest。

## 候选 identity

保存于 `/private/tmp/espocket-overlay-presentation-release/`，含 App、ELF、sdkconfig、lock、依赖 overrides、source-inputs 与 release JSON。前置候选保留。

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| espocket.bin | 11225424 | `c21597fd13ae3cb06a900ccffd8dbb77bd9352e2a200b93b4f35d858713e55be` |
| espocket.elf | 386528852 | `112a63348ef1ddbf7acde2ff2511d06be67fb9680d9e02997ec12f47c6872f00` |

应用分区剩余 24%；AEC 关闭、render profile 开启，与 023 配置相同。该产物不能作为 AEC／声学／唤醒词真机证据。

## 验证限制

Host adapter 替换 boot/status 及外围装配，Core 与 LVGL 类型是本地 stand-in；实际呈现与停止 implementation 不替换。真实 Core 请求队列、线程调度、帧输出、触摸和电源恢复仍须真机验收。启动单阶段阻塞及 250ms 要求保持归 023，不因此次 deepening 关闭。

未接设备、未部署、未提交或 push。既有 Quick Settings／Loading／023 未提交工作保留。
