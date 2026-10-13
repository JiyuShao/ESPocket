# 2026-10-13：生命周期命名与暂停快照

用户在 [接口审查](2026-10-13-app-interface-review.md)后授权优化生命周期命名与契约。本批保留 `on_start`、`on_stop`、`on_pause`、`on_resume`，优化新增原因通知及其参数，并修复同一链路中已复现的恢复重入漏洞。未实现 IMU、访问设备或烧录。

## 实现

- Core 0.8.4 增加独立补丁 `029-clarify-lifecycle-callback-contract.patch`；保持已归档 028 补丁字节不变。原始 managed_components 未手改，Core manifest 与 scheduler-candidate 同步维护完整 inventory 和补丁摘要。
- 新接口为 `on_pause_reasons_changed(AppContext &, const AppPauseReasons &)`，命名字段 `covered`、`screen_off`、`manual_pause` 在交付时从真实 AppRecord 读取。快照描述原因，不是采样、输入或活动授权，不新增生命周期 Owner/缓存。
- Native 默认新 hook 转发旧 `on_suspension_changed`，现有源码继续可编译；覆盖新 hook 时不重复调用旧 hook。这是源码兼容，不承诺预编译 C++ ABI 兼容。
- Runtime 首选 `on_pause_reasons_changed(snapshot_json)`，JSON 与 Native 结构同字段。当前 NativeValue 仅支持基本值，使用既有字符串桥，不扩大 Runtime backend。只有锁定 JavaScript backend 的明确缺函数错误允许回退旧三个 boolean；两者均缺少可运行，新 hook 的失败不会回退掩盖错误。除准确缺函数错误外，包含 `not found` 的异常与缺 App/module 均传播失败。
- IApp 注释明确四个生命周期 hook 执行初始化/清理/暂停/恢复工作，与 System 的 `on_app_started`/`on_app_stopped` 事实通知区分。开发契约提供完整调用时机与兼容规则。
- 原因回调返回后，在任何 resume 副作用之前重新核验同实例、前台、运行阶段、失败结果和最新暂停原因；重入新增覆盖时维持 Paused，不再误调用 on_resume。原因快照使用交付时最新事实，避免 on_pause 重入新增息屏后仍交付原请求旧值。

## 验证

- 为现有实际 Core 方法测试新增原因回调重入覆盖回归，修复前断言失败（exit 1，SIGABRT），修复后通过；Native/Runtime 两种执行路径均验证没有多余 resume。
- 同组新增 on_pause 重入新增息屏后的快照、原因回调切换前台后不恢复；原重叠原因、重复事件、旧实例、失败/异常及 resume 内新增覆盖回归保留并通过。
- `test_lifecycle_callback_contract.py` 执行生产 Native 默认 hook、Runtime 通知适配和真实 Boost JSON 序列化：新/旧/缺省 Native hook、Runtime 新优先/旧回退/两者缺省、命名 boolean 快照、false 与异常、缺 App/module、旧 hook 失败均通过。Runtime manager/回调为边界替身，不声称实际设备 JS 并发或主机连接已验收。

- 最终统一 `python3 scripts/check.py` 全部通过；跨模块组 187 tests、2 skipped。两项缺少 littlefs 的测试已使用前次候选的 `littlefs_py_venv/bin/python` 分别补跑并通过（内置 App 更新与 LittleFS 迁移）。日志 `/private/tmp/espocket-029-callback-host.log`。
- Runtime 通知测试随后补强三个字段各自单独为 true 的组合，覆盖命名快照与旧位置参数，防止相同 boolean 值掩盖字段交换；最终定向补跑通过，日志 `/private/tmp/espocket-029-callback-contract-test.log`。生产代码未因此变化。
- 原始 Core source inventory、全部 patch hash、最终 patched inventory 与两份 manifest 一致性复核通过；隔离构建的 Core 与定向测试工作副本逐字节一致。
- 最终 Markdown 检查通过 355 份文档，Git whitespace 检查通过。

最终完整隔离构建 v2 成功（exit 0），候选 `/private/tmp/espocket-029-callback-build-v2/candidate`，日志 `/private/tmp/espocket-029-callback-build-v2.log`。使用前次 v5 完整板级配置作为输入；归档保留原始、准备后与最终配置，最终 sdkconfig SHA-256 为 `fe9ede90d86c597d36f205b7679cc96241facfd193addd8a64b3eaeccd4940d2`。首个 v1 在依赖配置的 macOS sysctl 访问被沙箱阻止，未产出候选；v2 经已授权构建的自动审批后完成，不作为源码编译失败或物理证据。

- 本批 029 补丁 SHA-256：`026198757c2b2b71f12691694a7b03dc96bb4d73a3542be95a52007cbcc840fc`。
- 候选输入 fingerprint：`9710ddc944f0d9a1307ab4a4bf401068c955aac853ea1b3cd5306c0a3a86b346`，冻结输入复核通过。
- 候选 manifest SHA-256：`a98681bc2c2659f89a933e3f1d564ed4036bb0bfde7a1f1482f8428d766e8be9`；115 项 artifact 的大小和 SHA-256 全部匹配，flash_files 均在 inventory 中。
- `espocket.bin`：11,294,528 bytes（`0xac5740`），SHA-256 `40da041e9709b528550de3b9c8f97454ac5e1924013af015f2e91e17eeb6b1f0`；App 分区约 23% 空闲。

候选 `deployed=false`、`physical_validation=false`；fresh filesystem 不能作为保留设备数据的迁移镜像。新的 v2 候选替代含审查漏洞的初版 v5，两个历史候选身份和验证记录均保留。

## 范围与剩余门槛

本批没有改 AppExecutionState 的字段名、活动凭据或 timer/audio 策略参数；审查的其他接口优化仍是建议。IMU lease 撤销、共享采样与错误契约由 04 持有。本批不把命名/恢复修复认定为触摸、无线、声音或真机时序通过；物理条件仍归 09。
