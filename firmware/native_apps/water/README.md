# 水池 Native App

从 Launcher 打开“水池”。水面由 380 个粒子组成，小船随水面起伏；点击或拖动水面附近可搅动水流。首版使用固定向下重力，倾斜/摇晃等待真实 IMU 能力，页面明确提示倾斜暂不可用；触摸不冒充传感器数据。

粒子物理、小船和像素绘制改编自 [The-Badge](https://github.com/curisama/The-Badge/tree/76172dfaf0fa0ffedee91a61da3261afdde56ce3) 的 `main/apps/app_water.c`。来源锁定见 [Badge 来源](../badge/README.md)，MIT 许可见 [LICENSE](LICENSE)。没有迁入原作 Launcher、电源策略、全局 timer、IMU 模拟入口或原始 LVGL 输入路径。

## 实现边界

- `water_simulation.cpp`：每次打开独立的粒子、邻居网格、密度松弛、粘性、泡沫、小船浮力及 RGB565 绘制。保留原作粒子数、密度实测、颜色、船形和 64 行绘制分带。固定重力为原作 1900 px/s²；单次时间最多 100 ms、最多十个物理子步、每步最多 10 ms。没有改成正弦波或单列波形。
- `water_worker.cpp`：一个 App 工作线程，计算与绘制均在 GUI/System Owner 回调之外。两个 PSRAM 图像槽和一个合并更新，读取方持有不可变图像；没有空闲槽时跳过更新，避免队列增长。粒子状态约 40 KiB，两块 RGB565 图像及各自历史合计约 853 KiB；全部仅在运行期间分配。线程栈为 6 KiB PSRAM，独立工作线程不执行 Flash IO 或 GUI 操作。
- `water_content.cpp`：只在 App 的 Container 内绘制。GUI guard 内换入已完成图像、撤销旧图像缓存并保留新图像寿命；重绘区域为前后两帧占用范围的并集。每个图像槽保留自己的清理历史，不能把另一个槽的旧船/水面当成自己的历史。
- `water_input.hpp`：复用受控多点帧，以首个触点的 track identity 搅水；取消、暂停、换指和越出圆形区域后必须先全松开。只有被接受的真实搅水输入报告活动，动画不延长系统息屏时间。
- 暂停撤销待处理更新，取消当前计算并等待其收尾；恢复保留同次粒子进度、清除旧触摸且重置工作线程计时，不补算暂停时间。停止先确认工作线程退出，再卸载图像并释放资源；超时返回生命周期失败并保留 Owner，不能释放仍在使用的内存。`detach` 不等待工作线程，不存在 GUI 锁互等。
- 分配/线程失败可退出后重试；失败初始化立即释放已分配图像。App 不直接初始化 I²C/IMU，不持有原作 `port_perf_hold`，不增加平台 Core 或硬件接口。原作水池没有短音效，本 App 也不播放声音。

## 验证

`python3 -B -m unittest discover -s firmware/native_apps/water/test` 执行生产求解器、像素绘制、工作线程、输入和 App 方法。覆盖锁定原作粒子积分逐步 fingerprint 对比、100 帧搅水/长间隔/边界、每图像槽清理、真实 host 线程暂停/退出/重开、分配失败、不可变帧、输入取消、迟到 timer、缓存和图像寿命。

Host Core/GUI/ESP 边界替身不证明真实 LVGL 显示、ESP 调度、PSRAM 余量、持续帧率或触摸手感。完整候选和设备条件分别见 [028 本批记录](../../../.scratch/028-badge-native-app-migration/records/2026-10-13-water-touch.md)、[IMU 票](../../../.scratch/028-badge-native-app-migration/issues/04-imu-capability.md)和[真机票](../../../.scratch/028-badge-native-app-migration/issues/09-device-acceptance.md)。
