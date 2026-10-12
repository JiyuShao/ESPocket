# 07 — 迁移蓝牙遥控 Native App

**What to build:** 一个蓝牙遥控 Native App 提供触控板和空中鼠标两种模式，使用现有导航、GUI、IMU 与 BLE Owner。

**Blocked by:** [10 自绘与多点接入](10-native-content-and-pointer-seam.md)； [02 源码/GUI/触摸核查](02-source-and-gui-boundary.md)、[03 生命周期/活动](03-system-lifecycle-and-activity.md)、[04 IMU](04-imu-capability.md)、[05 HID](05-ble-hid-capability.md)。

**Status:** ready-for-agent

- [ ] 原作鼠标交互经 02 的公开触摸能力适配：移动、点击、拖动、滚动及两种模式；中文界面、连接状态与重试入口保持可操作，不迁入原作 Home handle。
- [ ] 首次手动配对，后续打开 App 尝试重连已配对电脑；开机不自动启动遥控。保留主机切换和按电脑保存灵敏度，设备管理以明确入口/确认忘记配对，取消隐藏长按清空。
- [ ] Quick Settings 暂停输入、释放持有状态并保留连接；息屏/Home 释放输入并断开。原因在 Paused 期间变化也生效，不能只依赖第一次 on_pause。
- [ ] 恢复同次 App 时保留模式，清除移动队列、拖动/长按状态和旧采样；必要校准期间不发送运动，不补发暂停期间输入。息屏恢复尝试重连，连接失败可重试。
- [ ] 全局系统手势优先，待决下拉不产生 HID 输入；取消/丢失触摸、模式切换、主机切换与实例停止不会留下按键或旧鼠标报告。
- [ ] 仅有效前台遥控输入报告活动；IMU 不可用时明确提示并可切回触控板，不注入模拟值。App 不关闭 Wi-Fi，不创建新的蓝牙/采样 Owner。
- [ ] on_stop 和失败清理撤销订阅、timer 与资源，迟到连接或输入不会作用于新实例；不增加 AI 鼠标/配对操作接口或后台遥控。
- [ ] host 验证上述输入状态与失败路径，运行 firmware 检查。macOS/Windows 实际体验归 [09](09-device-acceptance.md)。

## Comments

2026-10-09：原作 LVGL timers 不由 Core Paused 自动冻结，需显式适配。重连不是强制电脑接入，配对与 HID 报告需独立硬件证据。

2026-10-12：自绘与经过系统仲裁的多点接入由 [10](10-native-content-and-pointer-seam.md) 持有，属于本票实施前置。不得直接编入原作全局 LVGL/driver_data 路径来绕过该依赖。
