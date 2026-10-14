# 04 — 接入板级 IMU 能力

**What to build:** 在现有 HAL/Board/Service 边界接入板上 QMI8658 的加速度和陀螺仪能力，由 App 消费采样并实现玩法。

**Blocked by:** [02 驱动与接口核查](02-source-and-gui-boundary.md)。

**Status:** ready-for-agent

- [x] 已建立 `espocket_imu::Source` 公共契约；板级初始化、I2C 总线和采样资源归真实 HAL/Board Owner，App 不调用 BSP 或自行初始化驱动。当前板尚未声明 QMI8658，生产工厂明确返回 unavailable。
- [x] 公共能力明确单位（mg/dps）、坐标轴（PCB 固定坐标）、时间戳（微秒）、generation、有效性、采样与启停失败；不把原作注释/数值直接当成当前板验证结果。
- [ ] 采样启停与 Running Instance 的使用期限对应；暂停/停止/失败后无遗留采样或迟到回调。空中鼠标模式退出时释放陀螺仪资源，不改变其他使用方的资源。
- [ ] 错误与未就绪可区分，支持重试；没有 IMU 时无模拟数据注入生产路径。App 的降级提示与回退归 06/07。
- [x] 重力迷宫 host contract 覆盖失败回退、资源状态、单位参考值、重复序号、取消和触摸降级；驱动初始化成功、实际轴向、漂移与读数只在 [09](09-device-acceptance.md) 获得物理证据。
- [ ] 必要上游改动按 ADR-0016 锁定和隔离应用，运行 firmware 检查，记录公共接入方式。

## Comments

2026-10-09：已发现当前板级注册缺少 IMU，不能将此描述为硬件不支持。

实现记录：[2026-10-14 重力迷宫与 IMU 能力](../records/2026-10-14-gravity-maze-imu.md)。
