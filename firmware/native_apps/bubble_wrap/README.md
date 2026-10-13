# 泡泡纸 Native App

从 Launcher 打开“泡泡纸”。按下泡泡即爆破，可同时按多个泡泡；全部爆破后约 840 ms 自动补充。空白处长按约 550 ms 可提前补充。下拉 Quick Settings 与 PWR Home 由系统处理。

源码改编自 [The-Badge](https://github.com/curisama/The-Badge/tree/76172dfaf0fa0ffedee91a61da3261afdde56ce3) 的 `main/apps/app_games.c` 泡泡纸段落，以及 `main/port_esp.c` 的方波音色。原作版权与 MIT 授权保留在 [LICENSE](LICENSE)；精确输入保存在 [Badge 来源目录](../badge/README.md)。本 App 没有引入原作 Launcher、菜单、Back 按钮、全局 timer、codec task 或系统电源策略。

## 实现边界

- `src/bubble_model.cpp` 保留 466 px 画布、78 px 泡泡、82×70 六角布局、半径 178、22 ms 爆破音及 520 Hz 补充音；模型属于 App，不是平台布局特例。
- `src/bubble_content.cpp` 在本 App Container 下绘制原配色，只更新发生变化的泡泡与剩余数量；没有全局 screen 或事件直读硬件。
- `src/bubble_wrap_app.cpp` 使用 Core timer、App 所属自绘 token 和受控多点帧。暂停停止实际 model 更新、丢弃触摸、关闭短音效；恢复重置计时基准，同次泡泡状态保留，Home 后重新打开重置。
- `src/bubble_sound.cpp` 使用既有 AudioDecoder 的 Source/RequestOutput/OpenStream。仅在 Audio Owner 原子确认空闲时选择来源；一次最多一段 130 ms、16 kHz stereo PCM，12 KiB 有界队列和零入队等待。静音或忙时跳过，不改变系统音量。缓冲由 release callback 保留，回调只写独立原子完成时间，不访问 App；完成后异步保留一段音效时长供 HAL 消费尾部；停止立即关闭 stream 并释放 Source/binding。

受控帧取消时清除全部按压。相同 track_id 的移动不会变成第二次按下；新触点可爆破新泡泡。原 LVGL 事件回调改为 Core 20 ms 轮询，自动补充采用累计有效运行时间，不补算暂停时长。系统手势优先，首次挂载和恢复必须经过受控帧的全松开门槛。

## 验证

`python3 -m unittest discover -s firmware/native_apps/bubble_wrap/test` 执行实际生产 model/App 方法，验证多点按下、输入取消、补充计时、暂停与重新开始、停止后旧 timer 和启动失败清理。Host 的 GUI、timer、audio 边界替身不能证明实机绘制、手感、声音或线程时延；真机门槛归 [028/09](../../../.scratch/028-badge-native-app-migration/issues/09-device-acceptance.md)，其他五个游戏仍归 [028/06](../../../.scratch/028-badge-native-app-migration/issues/06-native-games-and-toys.md)。
