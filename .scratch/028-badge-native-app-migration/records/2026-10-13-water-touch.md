# 2026-10-13 水池触摸版与弹球移植修正

## 范围与来源

继续执行 [028/06](../issues/06-native-games-and-toys.md)。水池原作来源为锁定 The-Badge `76172dfaf0fa0ffedee91a61da3261afdde56ce3` 的 `main/apps/app_water.c`，源文件 SHA-256 `b5dd4c0a4790ea904da94a86f0066a6b261b13ee1b04b13064f04c80ddc938a1`；保留原始字节与 MIT 许可。

`firmware/native_apps/water` 提供 `espocket.app.water` 与独立 Root，保留 380 粒子流体、Clavet 密度松弛、粘性、邻居网格、连接水面/独立水滴、泡沫、船形/浮力与 RGB565 绘制。System 仅增加注册和依赖，本批不修改 Core、上游 managed_components 或补丁。

## 移植取舍

首版固定向下重力，真实触摸搅动附近水流；页面提示倾斜暂不可用。没有迁入 `water_sim_tilt`，没有以假 IMU 冒充倾斜。后续真实传感器依赖 [04](../issues/04-imu-capability.md)；用户可见说明与源码边界见 [App README](../../../firmware/native_apps/water/README.md)。

计算和绘制合并到 App 工作线程；工作线程不接触 GUI、AppContext 或系统导航。两个 PSRAM RGB565 图像槽、独立槽清理历史和一个合并更新取代原作共享全局数组/手工信号量。发布帧由 shared ownership 保持不可变，App 在 GUI guard 内撤销旧缓存并换入图像。物理子步和累计时间有界，无法绘制时跳帧而不增长队列；原作按上一轮耗时调子步的策略改为有界异步更新，实际设备帧率和功耗尚未证明。

暂停取消和清空待处理工作，确认当前计算收尾；恢复丢弃旧触摸且重新计时。停止确认线程退出后才卸载/释放；等待超时报告失败并保留资源，不沿用原作忽略信号量超时后直接释放的行为。detach 只撤销回调、缓存与图像引用，不等待需要 GUI 的线程。分配失败清理部分资源，线程仅在 App 打开期间存在。

## 弹球复核

对比锁定原作发现并修正：挡板每个子步应转动，原移植只转一次；漏了每步 14 px 球速上限；一次运动冲量之后仍需解算静态挡板碰撞，重叠时使用原作向上法线且第一个命中后结束挡板扫描。另修复两条 LVGL 线共借一个点数组、圆墙直径与物理接触范围不符，以及结束重开后一次松手仍不能控制挡板的问题。

新增生产模型与绘制回归验证以上路径；上一批三个测试没有覆盖这些条件，原候选只代表当时构建成功。历史 [弹球记录](2026-10-13-pinball-touch.md)的“最终重跑待日志收尾”不作为本批结果。本批候选包含修正，仍不能替代真机手感/声音验收。

## 离线验证与候选

水池专项最终 6 tests、弹球专项 5 tests 已通过。水池回归包含直接编译锁定源求解器，连续 40 步与生产粒子积分 fingerprint 一致；100 帧搅水/长间隔中粒子未越界且每槽未发现绘制范围外的残留像素。真实 host 工作线程验证满图像池时保留一个合并输入，并与生产 Simulation 的积分/图像结果一致。6 项水池测试在 AddressSanitizer 与 UndefinedBehaviorSanitizer 下再次全部通过。最后一次头文件修改后的统一检查、LittleFS 补跑及完整隔离构建均已通过，结果见下文。

真机持续帧率、PSRAM/内部 RAM 余量、暂停/PWR/下拉时延、触摸、船/水滴最终观感和倾斜仍待设备。[06](../issues/06-native-games-and-toys.md)总票保持未关闭，太阳系、重力迷宫与蓝牙遥控尚未完成。不部署、不配对、不发送 HID。

## 构建环境中断

首次 v1 与更新后的 v2 构建在临时磁盘空间耗尽时中断，v1 上游 Core 编译报告无法写入临时汇编文件，v2 工程暂存未完成；均没有成功候选。同期 sanitizer 与部分全仓检查也受 `Errno 28` 中断，不计通过。保留日志并提炼本段事实后，清理本次失败 workspace 和上一批弹球可再生的 `firmware/build`；保留弹球 candidate、配置、输入 inventory/补丁及最终产物。后续在新 workspace 串行完整重跑。

重跑 v3 在水池目标编译发现 `lvgl.h` 不声明 `lv_image_cache_drop`；补上锁定 LVGL 的 `src/misc/cache/instance/lv_image_cache.h`，不修改上游，也不放宽编译诊断。先用 v3 保存的真实 Xtensa 编译参数编译当前生产源，再冻结到新完整构建。Host 内容测试替换了 LVGL 边界，因此未捕获这一头文件可见性问题；v3 没有成功 candidate。

v3 头文件修正后的单文件真实 Xtensa 编译已通过。统一检查在清理磁盘后完整通过（264 tests，跨模块组 187 tests 的 2 skipped）；两项 LittleFS 已使用构建的 Python 环境分别补跑各 1 test 通过。最后一次头文件修改后继续重跑统一检查，并以 v4 冻结的完整构建结果作为最终候选。

为最终归档预留空间，v3 失败 workspace 的可再生 `firmware/build` 随后清理；冻结产品源码、配置、输入快照及外部失败日志保留，真实目标编译参数另存 `/private/tmp/espocket-028-water-v3-compile-commands.json`。清理不会修改 v4 的冻结输入。

## 最终结果

最后一次源码修改后 `python3 scripts/check.py` 完整通过，共 264 tests（跨模块 187 tests，其中 2 skipped 已在 LittleFS 环境独立补跑各 1 test）。水池 6 tests、弹球 5 tests 通过；水池 6 项 sanitizer 回归通过。Markdown 检查通过 362 文件。

完整隔离构建使用 ESP-IDF 6.0.1、已验证 Waveshare 1.75C 板级配置和 production 补丁；构建脚本核验精确依赖锁、组件选择、配置及不可变输入。最终候选仅为 `/private/tmp/espocket-028-water-build-v4/candidate`。

| 项目 | 结果 |
|---|---|
| Input fingerprint | `ba16f9c7386b76e595b196b5a7fc49ec45b153971acdb5b267b5b186c1c0f993` |
| espocket.bin | 11,348,080 bytes |
| SHA-256 | `d0113083d28cfa230ec1caf60f08ca7d73c108507f044a67e4299ee672f1bbca` |
| App 分区余量 | 23% |
| 归档验证 | 115 artifacts 的大小/hash 全部匹配；86 个相关 App/System 冻结输入与当前源码匹配 |
| 部署/物理验收 | `deployed=false`，`physical_validation=false` |

候选保存 ELF、Flash 镜像、配置、lock、原始/准备输入、完整补丁字节和输入证明；LittleFS 是 fresh filesystem，不能覆盖设备已有数据。本批不部署。最终日志保存在 `/private/tmp/espocket-028-water-build-v4.log`、`/private/tmp/espocket-028-water-final-v4-checks.log` 与 `/private/tmp/espocket-028-water-sanitizers-final.log`；两个 LittleFS 日志为 `/private/tmp/espocket-028-water-builtin-update.log`、`/private/tmp/espocket-028-water-littlefs-migration.log`。太阳系、重力迷宫、IMU、BLE HID、蓝牙遥控和真机门槛继续保持未完成。
