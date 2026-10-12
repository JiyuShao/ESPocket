# 10 — App 所属自绘挂载与多点输入

**What to build:** 在真实 GUI Runtime/LVGL Owner 内实现 02 选定的有界 Native 自绘挂载，复用 Display 多点快照并保留系统输入仲裁。

**Blocked by:** [02 来源及接入核查](02-source-and-gui-boundary.md)。

**Status:** resolved

- [x] 实现 [最小公开 API 与失效契约](../records/2026-10-12-source-and-boundaries.md#选定的最小自绘接入方案待实现)，按 App document/container 验证身份；不暴露私有 handle、全局 screen 或全 Runtime 访问。
- [x] 通过 GUI 调度/thread guard attach/invoke/detach，token 绑定本次挂载；旧 token、旧节点、节点重建、实例停止后访问拒绝。
- [x] 父节点 unload/destroy 前撤销 token、停 timer/事件、清理自绘子树；挂载部分失败与清理失败不泄漏回调，不假报成功。
- [x] 复用 Display TouchSnapshot/MultiTouchPointerManager；顶部手势消费、覆盖、息屏与旧输入取消后无 App/HID 操作，不二次读取硬件、不复制输入 Manager。
- [x] 用实际生产方法验证失败、重复关闭、迟到 invoke、节点替换、两指变化与系统取消；兼容现有 JSON/Runtime App GUI。
- [x] 必要补丁按 ADR-0016 锁定精确版本/hash 和移除条件；独立完整构建与文档检查通过，真实触摸/绘制验收仍归 09。

## Comments

2026-10-12：02 核查表明既有 Canvas API 不能承载水池/天体动态绘制，且原作全局顶层和 driver_data 路径不符合共同 App contract；此票持有必要公共 seam，不由 System 新建 GUI Framework，也不在游戏中偷取 backend 对象。


## Resolution

2026-10-12：在真实 GUI Interface、GUI LVGL、System Core 和 CircularShell Owner 中实现 App-owned native content seam 与受控多点帧。接口、失败清理、token 失效、预加载 DOM 停止清理和输入取消回归已通过；完整隔离构建和离线检查证据见 [实现记录](../records/2026-10-12-native-content-implementation.md)。真实绘制、触摸手感及设备验收仍由 09 持有。
