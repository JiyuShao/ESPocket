# 太阳系 Native App

从 Launcher 打开“太阳系”，选择月球、地球、太阳或木星。用手指拖动球体，可旋转、翻越极点或从边缘滚动轴向；松手后按原作摩擦衰减并停下。系统 Back 返回选择列表，Home 后重新打开从列表开始。这里保留的是原作 Orbit 球体玩具，不是行星轨道模拟。

来源为 [The-Badge](https://github.com/curisama/The-Badge/tree/76172dfaf0fa0ffedee91a61da3261afdde56ce3) 的 `main/apps/orb.c` 和 `app_games.c` 中的球体菜单。参考输入见 [Badge 来源](../badge/README.md)，改编代码保留 [MIT 许可](LICENSE)。四份 NASA RGB565 材质逐字节复制至本 App 的 resources，作者及图像出处见 [NOTICE](NOTICE)；NASA/JPL 不为本产品背书。

## 实现边界

- `orbit_motion.cpp` 保留原作经度、倾斜、侧倾、触点位置影响和释放惯性。只有接受的真实点击/拖动报告活动；动画不延长息屏时间。
- `orbit_renderer.cpp` 保留 466px 画布、206px 半径、屏幕空间光照、太阳自发光、地球亮度提升、极点投影、UV 缓存和移动时的 2×2 绘制。停止时补一张清晰图像，此后不再绘制。没有生成替代纹理或使用假 IMU。
- `orbit_worker.cpp` 是 App 私有工作线程，只做查表准备和像素绘制，不接触 AppContext、GUI 或导航。一个合并姿态和两个不可变 RGB565 图像槽限制待处理工作；图像都被持有时等待，不增长队列。材质/表约 1.4 MiB、图像约 848 KiB，仅球体页期间分配，线程使用 6 KiB PSRAM 栈。
- `orbit_content.cpp` 在既有自绘挂载内显示中文列表或已完成图像，交换图像前撤销旧缓存；detach 同步断开回调和图像引用，不等待线程。交互由 `orbit_input.hpp` 读取系统仲裁的受控触点，取消/换指/暂停后必须全松开；不安装原始 LVGL 点击回调。
- App 声明 `root` 与 `globe`，通过既有 PageNavigator Push/Back 改变显示，不建立第二个导航栈。System 仅增加组件依赖、注册和导航装配；不修改 Core、HAL 或 managed_components。
- Quick Settings/息屏暂停绘制，确认进行中的工作收尾；恢复保留球体姿态、清除旧惯性和触摸，重新计时。停止先确认线程退出，再卸载/释放；超时保留 Owner 并报告失败。分配失败可 Back 后重试。原作没有音效或 IMU 依赖。

## 验证

`python3 -B -m unittest discover -s firmware/native_apps/solar_system/test` 执行生产 App 方法、PageNavigator、输入、运动、渲染、内容和真实 host 工作线程。覆盖锁定源逐像素及运动对照、四材质/极点/侧倾、惯性停止、取消、暂停/恢复、图像寿命、分配失败、GUI 派发失败重试和旧实例 timer。

Host 替换 Core/GUI/ESP 边界，不证明真实 LVGL 显示、PSRAM 余量、帧率、功耗或触摸手感。完整构建与设备条件分别见 [本批记录](../../../.scratch/028-badge-native-app-migration/records/2026-10-14-orbit-native.md)及 [028/09](../../../.scratch/028-badge-native-app-migration/issues/09-device-acceptance.md)。
