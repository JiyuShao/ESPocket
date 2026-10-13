# 2026-10-13 弹球触摸版

## 范围与来源

继续实施 [028/06](../issues/06-native-games-and-toys.md) 的弹球 Native App。来源为 The-Badge `76172dfaf0fa0ffedee91a61da3261afdde56ce3` 的 `main/apps/app_games.c` 弹球段落；原始来源目录和 MIT 许可保持不变。

`firmware/native_apps/pinball` 使用 `espocket.app.pinball` 身份和 Root。System 只负责注册，App 自己持有模型、绘制、timer 和音效调用；本批不改 System Core、GUI 上游组件或补丁。

## 移植取舍

保留原作圆形球台、五个碰撞球、四个目标、两只挡板、三颗球、目标奖励、底部排球口、重力/阻尼和挡板运动的物理顺序。原作的 IMU 倾斜操作暂未接入，首版改为受控多点触摸：左/右半区控制对应挡板，双指可同时按下；没有传感器时仍可玩，不使用假 IMU 数据。

原作全局状态改为 App 实例状态；固定 20 ms 步进、单帧最多五步、累计时间最多 200 ms。暂停清除输入与部分步进余量，恢复重置时钟；停止释放全部资源，迟到 timer 通过 timer ID 和 Running Instance 身份拒绝。碰撞/目标/挡板音效通过共享 `espocket::ShortEffect`，调用方使用独立音源名。

## 离线验证

三个 pinball host 测试执行生产 `Model` 与 `PinballApp` 方法，覆盖碰撞得分、目标全部落下奖励、挡板双触点、排球口/生命/结束、定步上限、取消/重复帧、暂停恢复、启动失败清理、停止后旧 timer 和新实例重置。真机触摸手感、音效、Quick Settings/PWR 竞争、持续帧率及后续倾斜控制仍待 [028/09](../issues/09-device-acceptance.md) 与 [028/04](../issues/04-imu-capability.md)。


## 构建结果

`python3 scripts/check.py` 的最终重跑待日志收尾；弹球专项 3 tests 已通过，文档检查通过 360 文件。完整隔离构建使用 ESP-IDF 6.0.1、已验证板级 sdkconfig 和 production 补丁集合，构建脚本已核验依赖锁、补丁组件选择、配置和候选输入。候选目录为 `/private/tmp/espocket-028-pinball-build-v1/candidate`，归档 115 个 artifacts；input fingerprint 为 `c1eca412230a42d83e776d97035382537969f89d57b4788750c2e4f4aa69a628`。`espocket.bin` 为 11,323,472 bytes，SHA-256 `c2fb8e1e4e39d3ce506ec5e2e990f4c0797953f04c25128d3cf7634f4d5d5697`，App 分区剩余约 23%。`deployed=false`、`physical_validation=false`，文件系统为 fresh filesystem，不能覆盖设备现有数据。
