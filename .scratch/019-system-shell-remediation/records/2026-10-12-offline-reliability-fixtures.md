# 2026-10-12 — 离线可靠性测试入口

## 范围与实现

用户明确没有真机，要求先完成可离线可靠性工作再继续 028。当前新增[测试入口](../../../firmware/test/device/fixtures/reliability/README.md)及构建选项 `--reliability-fixture`；普通入口和产品源码没有加入测试分支，原 managed_components、生产 dependencies.lock 和 NVS 偏好不修改。

测试注入只发生在新的隔离副本、输入冻结之前。九种模式覆盖产品初始化获得主题/Card/Shell 后失败、Shell/PWR 启动后失败、未知主题/应用失败/默认失败，以及外部协调的完整 System 同对象 stop→start / deinit→init 各三轮。App_main 协调不属于 System Owner 或 USB Adapter 的寿命，停止 USB 后仍能驱动下一轮。每轮启动 Native/Runtime Hello，产生键盘、active/queued 系统 Dialog；停止后旧请求结果必须拒绝，状态和 heap free/largest 由日志观察。

Core 正常 App stop 会先交付键盘取消，因此夹具允许这次 confirmed=false；禁止的是旧请求的确认结果或停机后仍接受请求。新增协调器 host 回归编译实际夹具入口、替换外围 System/堆/RTOS，验证六轮及正常取消可完成，故意保留旧请求时必须失败。它只证明夹具断言有效；真实 Core 清理由已有生产方法 host tests 验证，不能把 fake System 当产品线程证据。

脚本测试验证明确模式、原工程不变、seam 漂移/重复注入拒绝。构建入口拒绝与 M2/包验收/Card/reclaim 自动夹具混开，将模式同时写入 patch-inputs 与候选 manifest。没有增加统一生命周期/rollback Manager。

## 最终构建证据

最终目录：`/private/tmp/espocket-reliability-20261012-lifecycle-v4/candidate`。

- 模式 lifecycle，完整生产补丁集；配置输入为 027-v3 已验证的完整板级 sdkconfig，使用 ESP-IDF 6.0.1 / Python 3.11。
- Input fingerprint：`01f9f7029c53c81fab2dcae6226e33e31283cfa1cafa61ae28e12cddb7c82c75`。
- App 11,243,232 bytes，SHA-256 `aafd18e2613045fdcda89ec8c7058e074f6c7fc879ff458b077578c7971212fa`。
- 108 个归档文件逐项大小/SHA-256 复核；deployed=false、physical_validation=false。
- 完整构建日志 `/private/tmp/espocket-reliability-20261012-build-v4.log`。
- 九种模式另使用本次 compile_commands 的实际 Xtensa 编译参数分别编译注入后的 system.cpp/app_main.cpp，全部通过；日志 `/private/tmp/espocket-reliability-20261012-modes.log`。这不是另外八份已链接候选，也不是故障设备执行结果。

最初构建因 ESP-IDF 的 sysctl 被沙箱拒绝而失败；解除该环境限制后，第二次因 checkout 的旧 sdkconfig 缺板级 HAL 开关失败，未降低校验门槛。第三次在发现夹具应允许正常键盘取消后主动终止，未作为可验收候选。v4 冻结修正后的源码重新完整构建，旧目录和失败记录保留。

## 仍未验收

019/01–02、05 保留原物理条件：逐 Core 分配点/GUI 锁/真实 callback 竞争不在这九种注入的完整覆盖承诺中；后台工作停止、内存变化、失败画面、主题实际保存/重启与显式硬件重启仍需真实设备。测试入口具备不等于这些票 resolved。

该候选是测试固件，不替代 027 的普通验收候选。LittleFS 是 fresh filesystem，不允许直接覆盖用户数据；将来各注入模式须单独构建并按原票备份、部署、记录、恢复普通候选。无设备时未刷机、未访问串口、未配对或发送 HID。

028 已继续来源/接入核查，见[来源与边界记录](../../028-badge-native-app-migration/records/2026-10-12-source-and-boundaries.md)；原作 28 个文件已锁定保留，公开自绘/多点 seam 和七个 App 的实际实现仍由 028 后续票持有。

## 最终检查

`python3 scripts/check.py` 最终通过，共 237 项，2 skip；日志 `/private/tmp/espocket-reliability-20261012-check-final.log`。该轮 host discovery 后追加的协调器自身行为用例另以 `test_reliability_fixture.py` 定向运行，4 项全部通过，包括正确停止取消与旧请求保留的相反结果。来源锁测试通过；最终 Markdown 检查 348 个文件通过。后续来源核查/host 断言/收尾文档没有改变 v4 注入入口，但不是回写既有冻结输入；候选身份以其归档 manifest 为准。
