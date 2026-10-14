# 重力迷宫与 IMU 能力（2026-10-14）

## 结果

- 新增 `firmware/components/espocket_imu`，对 App 暴露最小 `Source` 契约：`start/stop/pause/resume/read`。
- 样本单位固定为加速度 `mg`、角速度 `dps`，时间戳为微秒；轴是 PCB 固定坐标，样本携带 `generation` 和加速度/陀螺仪有效性。
- 当前 Waveshare 1.75C 板级 YAML 只有共享 `i2c_master`，没有 QMI8658 设备声明。工厂因此返回明确的 `unavailable`，没有把 QMI8658 依赖或 raw I2C 读取放入 App。
- 新增 `espocket.app.gravity_maze`：保留原作圆形滚珠、洞、边缘反弹和触摸降级；有真实样本时按板级坐标映射倾斜，有效样本时间戳倒退或重复时丢弃。
- 启动失败、采样失败、暂停、停止都会回收/停用当前 Source；恢复会重新尝试启动，失败时继续使用触摸控制。

## 验证

- `firmware/native_apps/gravity_maze/test/test_gravity_maze_model.py`：2 项通过，覆盖触摸降级、洞计分、边缘反弹、单位参考、重复序号与取消。
- `python3 scripts/docs/check.py --markdown`：通过。
- `python3 scripts/check.py`：187 项 host 测试通过；首次运行的 Markdown 检查在 App README 建链前失败，补链后单独通过。隔离 ESP-IDF 构建受当前 macOS sandbox 禁止 `psutil` 枚举进程影响，未以失败构建宣称源码错误。

## 待真机

QMI8658 是否实际焊接、驱动初始化、I2C 地址、轴向/符号、漂移、采样功耗、倾斜手感和真实帧率仍由 [09](../issues/09-device-acceptance.md) 验收。当前构建不可部署到设备。
