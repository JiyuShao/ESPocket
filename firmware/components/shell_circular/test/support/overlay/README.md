# Shell Overlay host adapter

`test_overlay_presentation.py` 编译真实 CircularShell 声明、私有呈现状态、完整 `shell_overlay.cpp`（含实际 Owner timer 与 on_stop）、Keyboard／Dialog 绘制和 Gesture implementation。测试不读取并拼接生产源码，不重声明 CircularShell，不读取它的私有状态；场景经现有 public interface 操作，观察 GUI sink 和 Host 结果。

这里的 Brookesia 类型与 LVGL sink 是 host adapter。`shell_host_fixture.cpp` 替换启动时的硬件／资源装配与外围状态刷新，创建实际呈现状态；启动失败与真实绑定的生命周期仍由现有专项回归和固件构建验证。此夹具不替代真机 Core 请求队列、LVGL 线程调度、显示帧输出或物理触摸证据。

GUI sink 保留创建、隐藏、删除和回调语义，允许注入 allocation／lock／flow failure；Host 验证 Core 查询、显示读取和结果交付不在 GUI 锁内。保持呈现稳定时，维护 tick 不应反复请求 GUI 锁。
