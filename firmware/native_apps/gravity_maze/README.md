# 重力迷宫

重力迷宫复刻 Badge 原作的圆形滚珠玩法：滚珠受倾斜加速度推动，撞击内圈反弹，进入洞后生成下一个洞。当前板级配置尚未声明 QMI8658，因此启动时会显示“倾斜不可用 · 触摸控制”，触摸是明确的降级输入，不会伪造 IMU 样本。

`espocket_imu::Source` 是 App 消费的最小能力边界。它规定加速度单位为 mg、陀螺仪单位为 dps、时间戳为微秒，样本带有 generation 和有效性。板级 Owner 负责总线、驱动和采样资源；App 不初始化 I2C 或读取 raw driver data。暂停和停止会释放采样使用权，读失败会回退到触摸并保留可重试的能力状态。

Host tests cover bounded integration, rim reflection, hole scoring, sequence deduplication, cancellation, and touch fallback. They cannot establish real axis direction, drift, sensor presence, or frame rate; those remain in the device acceptance ticket.
