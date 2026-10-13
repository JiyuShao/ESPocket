# 打砖块 Native App

从 Launcher 打开“打砖块”，点击开始后先松手，再拖动屏幕转动底部环形挡板。五关依次改变球速、挡板长度、砖块排列、耐久砖与旋转障碍。每轮三条生命；失误后重建当前关卡并等待点击，生命耗尽回到第一关，全部通关后点击重新开始。当前为触摸版，倾斜控制等待 [028/04 IMU 能力](../../../.scratch/028-badge-native-app-migration/issues/04-imu-capability.md)。

源码改编自 [The-Badge](https://github.com/curisama/The-Badge/tree/76172dfaf0fa0ffedee91a61da3261afdde56ce3) 的 `main/apps/app_games.c` 打砖块段落。原作 MIT 授权见 [LICENSE](LICENSE)，锁定原始输入见 [Badge 来源目录](../badge/README.md)。原作 Launcher、菜单、Back/倾斜按钮、全局 timer、codec task 与电源策略没有迁入。

## 实现边界

- `brick_model.cpp` 持有每个实例独立的关卡、球、砖块、生命与拖动状态，保留 466 px 画布、原配色、圆墙/环形挡板、碰撞次序与五关参数。固定 20 ms 物理步进，单帧最多五步，累计待处理时间最多 200 ms，避免持续迟到帧堆积无界追赶。
- `brick_content.cpp` 只在本 App Container 下绘制，复用 36 个砖块对象，更新变化项及移动的小球/障碍；没有全局 screen、原始 LVGL 输入读取或另一个导航栈。中文文字继承 Container 指定的产品 `default` 字体及中文 fallback。
- `brick_breaker_app.cpp` 使用既有 Core timer、自绘挂载和受控触摸帧；取消、重复序号与拖动触点替换不会产生新操作。启动点击不用于转动挡板；挂载、关卡重建和取消后先等待全松开。
- Quick Settings/息屏由系统触发暂停，App 保留进度、清除输入及未满一物理步的计时，关闭音效；恢复重置时钟，不补算暂停时间。Home/停止释放 timer、自绘挂载和音频资源，重新打开从第一关开始。动画不报告用户活动。
- 两个 App 复用 [App 短音效适配](../../components/espocket_app_effects/README.md)，各自传入独立音源身份。保留原作 600 Hz/30 ms 耐久砖、900 Hz/40 ms 普通砖、700 Hz/25 ms 障碍、500 Hz/30 ms 挡板音。Audio Owner 忙或静音时跳过，不抢语音、不修改系统音量；同一帧仅播放首段音效。

## 验证

`python3 -m unittest discover -s firmware/native_apps/brick_breaker/test` 执行生产 model、App 生命周期与自绘方法，覆盖五关布局、碰撞方向/推出、耐久砖、生命/通关、计时、触点取消、暂停/恢复、旧 timer、启动失败和局部绘制。LVGL/Audio/Timer 边界替身不能证明真机手感、声音或调度时延；物理验收仍归 [028/09](../../../.scratch/028-badge-native-app-migration/issues/09-device-acceptance.md)。
