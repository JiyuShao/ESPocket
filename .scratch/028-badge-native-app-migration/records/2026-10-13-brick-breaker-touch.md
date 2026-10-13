# 2026-10-13 打砖块触摸版

## 范围与来源

用户授权继续下一步，实施 [028/06](../issues/06-native-games-and-toys.md) 的独立打砖块触摸版。精确来源为 The-Badge `76172dfaf0fa0ffedee91a61da3261afdde56ce3` 的 `main/apps/app_games.c`，保持锁定原始字节不变及 MIT 归属。

`firmware/native_apps/brick_breaker` 以 `espocket.app.brick_breaker` 可见身份和 Root 安装，System 仅增加装配注册；本批不修改 Core、GUI 上游组件或补丁。App 持有纯实例模型、自绘与资源，使用既有暂停/恢复、timer、自绘挂载、受控触摸和活动凭据。

## 移植取舍

保留原作五关参数、圆墙/环形挡板、砖排列和配色、耐久砖、旋转障碍、三条生命、每关得分、碰撞反射/推出、球速上限及 20 ms 固定步。源码实际五关砖数为 14/20/10/17/20，耐久砖为 0/4/4/8/9；以真实布局公式与表为准，不能以原注释的历史砖数替换当前源码。

原作全局状态变为 App 实例数据，LVGL 事件改为系统仲裁后的 track_id/sequence 帧。单帧仍最多五步，每次新增时间限 200 ms，并将待处理累计时间也限至 200 ms，避免连续慢帧产生无界追赶。覆盖/息屏清除拖动及未满一步的累计时间，恢复重置时钟；丢球/升级直接重建纯模型并等待点击，自绘复用对象，避免原 LVGL deferred callback 删除运行中的对象。开场点击不操作挡板；取消/关卡变化后要求全松开。

中文提示由 App 绘制并继承 JSON Container 的产品 default 字体，不复制字库。原作菜单、Back/Home handle、倾斜切换、原始 IMU 读取、codec task 和系统电源策略未迁入；触摸模式可玩，倾斜控制依赖 [04](../issues/04-imu-capability.md)。

两个真实 App 共用 `espocket::ShortEffect`，保留原短音效适配并让调用方传入各自音源名；旧回调只持有 PCM/独立原子完成时间，不访问 App。真实 Audio Owner 原子拒绝占用来源，音量/静音归原 Owner，同一帧只播放首段音效。共享范围限于真实复用的适配，没有新增 GameManager 或 App 框架。

## 验证与候选

首次隔离构建 v1 在 ESP32 GCC 的 `uint32_t`（unsigned long）与 `200U`（unsigned int）模板推导处失败；修复为显式 `std::min<uint32_t>`，没有放宽编译诊断。Mac host 的整数 typedef 不同，专项回归不能替代目标完整构建。v1 保留在 `/private/tmp/espocket-028-bricks-build-v1`，没有生成可交付 candidate。修复后四个打砖块专项回归再次通过，并通过真实 Xtensa GCC 参数的单独目标编译，随后使用新的 v2 隔离目录完成完整构建。

首次统一检查的全部 14 个测试组通过（共 253 tests，其中跨模块组 187 tests、2 skipped）。两个跳过项因默认 Python 缺 littlefs，已用上一完整候选的 `littlefs_py_venv/bin/python` 补跑 `test_builtin_app_update.py` 与 `test_littlefs_migration.py`，各 1 test 通过。该次命令仅因两个新 README 缺少文档入口链接返回失败，已补齐并独立通过 Markdown 检查；修复目标编译类型后再执行最终统一检查。


最终 `python3 scripts/check.py` 返回 0，全部组通过（253 tests；跨模块组 187 tests、2 skipped，环境补跑结果如上），Markdown 358 文件通过。打砖块四个测试执行生产模型、App 方法与自绘方法，覆盖五关真实布局/难度、砖/墙/挡板/障碍碰撞、耐久砖、生命/通关、固定步/单帧上限、触点序号/跟踪/取消、暂停余量/时钟、停止后回调、启动失败及变化项绘制；音效迁移回归执行生产适配并核对不同调用方音源身份。边界替身不证明物理 GUI/声音/线程时延。

完整隔离构建使用 ESP-IDF 6.0.1 与上一已验证候选的板级 sdkconfig，选择 `esp32_s3_touch_amoled_1_75c`，精确应用现有 production 补丁；无新增/重写补丁。构建脚本核验锁、配置、组件选择及冻结输入后归档，另核验所有 115 artifacts 的文件大小/SHA-256及 29 个当前非文档 App/适配/注册输入与候选一致。

| 候选事实 | 值 |
|---|---|
| 目录 | `/private/tmp/espocket-028-bricks-build-v2/candidate` |
| Input fingerprint | `5c3bfbf91b93cb125b9dae0f393c0e5c46b0660648f25dc71a4ceb4cc58cbdb4` |
| espocket.bin | 11,309,296 bytes，App 分区剩余 23% |
| espocket.bin SHA-256 | `24fc4057581b614b146cf4605e456d18507c91448d0ca2959ea7ede709d6b133` |
| sdkconfig SHA-256 | `fe9ede90d86c597d36f205b7679cc96241facfd193addd8a64b3eaeccd4940d2` |
| 部署/物理验收 | `deployed=false`、`physical_validation=false` |
| 文件系统 | fresh filesystem；不是设备迁移镜像，不能用来覆盖现有用户数据 |

最终日志保存在 `/private/tmp/espocket-bricks-host-check-final.log` 与 `/private/tmp/espocket-bricks-build-v2.log`。候选保存精确源码 inventory、配置、依赖锁、补丁字节与产物 hash；记录更新不改变候选身份。

## 待验

未部署、未访问设备。中文最终显示、触摸手感、下拉/PWR 竞争、声音和持续帧率待 [09](../issues/09-device-acceptance.md)；倾斜控制待 04。06 六游戏总体票及 08/09 的其他条件保持未关闭。
