# 弹球 Native App

从 Launcher 打开“弹球”，点击开始后先松手。屏幕左、右两侧分别控制两只挡板，支持同时触摸；球撞击五个碰撞球和四个目标会得分，四个目标全部落下后获得奖励并复位。三颗球耗尽后点击重新开始。

源码改编自 [The-Badge](https://github.com/curisama/The-Badge/tree/76172dfaf0fa0ffedee91a61da3261afdde56ce3) 的 `main/apps/app_games.c` 弹球段落。原作 MIT 授权见 [LICENSE](LICENSE)，来源锁定见 [Badge 来源目录](../badge/README.md)。原作菜单、Back/Home handle、全局 timer、codec task 和电源策略没有迁入。

## 实现边界

- `pinball_model.cpp` 持有每个实例独立的球、碰撞球、目标、挡板、得分和生命状态，保留圆形边界、底部排球口、五个碰撞球、四个目标、三颗球、重力、阻尼、挡板运动和固定 20 ms 物理步。
- 触摸帧由 System Core 仲裁；左半区按下左挡板，右半区按下右挡板，双指可同时操作。取消、重复序号、暂停和关卡/重开都要求全松开后再接受输入。倾斜控制保留为后续 IMU 能力增强，首版没有用模拟数据冒充传感器。
- `pinball_content.cpp` 只在 App Container 下绘制，使用圆墙、彩色碰撞球、目标、线段挡板和球；没有全局 screen、原始 LVGL 输入读取或第二个导航栈。
- Quick Settings/息屏触发既有暂停回调，App 清除挡板输入与未满一步的计时，恢复重置时钟，不补算暂停时间。Home/停止释放 timer、自绘挂载和短音效资源，重新打开从 Root 开始。动画不报告用户活动。
- 复用 [App 短音效适配](../../components/espocket_app_effects/README.md)，碰撞球、目标、挡板和掉球声音遵守 Audio Owner 的忙/静音策略，不抢语音或修改系统音量。

## 验证

`python3 -m unittest discover -s firmware/native_apps/pinball/test` 执行生产模型和 App 生命周期方法，覆盖碰撞、目标奖励、挡板、掉球/结束、固定步、输入取消、暂停恢复、启动失败、停止后旧 timer 和实例隔离。边界替身不能证明真机手感、声音或调度时延；物理验收仍归 [028/09](../../../.scratch/028-badge-native-app-migration/issues/09-device-acceptance.md)。
