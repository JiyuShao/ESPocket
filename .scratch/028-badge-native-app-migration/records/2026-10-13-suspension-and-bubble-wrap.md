# 2026-10-13：暂停、活动准入与泡泡纸

本批按用户“可以的，完整帮我实现”授权，完成 028/03 与首个泡泡纸 App，验证完整 Native 接入路径。未操作设备、配对主机、发送 HID 或烧录；六游戏总票、IMU/BLE 与物理门槛分别保留。

## 实现

Core 028 补丁在真实 AppRecord 保存 start instance、覆盖/息屏/manual 原因、失败结果。同步与分阶段启动都分配新身份；首次暂停撤销 Running，再发 on_pause 和 reason callback，末次恢复检查同一前台身份，不改变 active App。App callback 返回失败或异常后保持 Paused；Home 仍可停止。Runtime reason callback 为可选三 boolean 参数，不要求修改旧包。

System 只接通 Quick Settings/Display 事实和既有前台恢复投影；Paused 同实例仍有效。Shell activity_generation 沿原 idle 路径更新。Core 检查旧 instance、暂停/Running 状态、前台和 input epoch，迟到活动拒绝，不唤醒屏幕。Shell、Card 和持续 Service 没有新生命周期 Manager。

普通 periodic timer 暂停不补发；one-shot deferred 在原 timer record 保存，恢复后的 Core maintenance tick 执行一次。已有 on_event 保留 Running/Paused 分发，Runtime 导航 completion pump 显式 completion=true，保留 Promise 清理。聊天 discovery/navigation/network/history 的普通 timer 无 ID 特例，一次性 timer 不再因暂停到期丢失；计算器没有新暂停依赖，Settings 使用原生命周期代理；键盘/Dialog 仍受 Core 请求身份与 Shell 仲裁，新增 Paused 不替换它们的 Owner。

泡泡纸在 firmware/native_apps/bubble_wrap，独立可见身份/Root、中文名称、原六角画面与配色、按下即爆、多点、全部爆破约 840 ms 补充、空白长按补充。model、LVGL content、短音效适配都属于 App。原 LVGL callback/timer/codec task 转为 Core 20 ms 受控帧轮询；没有原作菜单、Launcher、Back 或硬件直读。暂停清输入并停止有效时间，恢复重置时间基准，停止释放 mount/timer/audio，重开重置泡泡。

AudioDecoder 0.8.2 新补丁为公开 Native set_active_source 增加默认关闭的 only_if_idle；检查与选择使用同一个 Owner mutex，旧调用兼容。短音效低优先 Source、一次一段、最长 130 ms、16 kHz stereo PCM、12 KiB 队列、零入队等待；静音或 Audio 输出忙时跳过，不改系统音量。borrowed buffer 由 release callback 保留，callback 只写独立原子时间，不引用 App；App 异步等待一段音效时长后释放，暂停/停止立即清理。真实输出尾部与播放效果仍待设备。

所有原始 managed_components 保持原字节；Core/Audio 精确补丁与 manifest inventory 同步，scheduler-candidate 与 Core manifest 一致。

## 验证与候选

- 新增生产 Core 生命周期/活动测试：重叠原因、重复事件、wake 仍覆盖、手动原因、前台切换、停止/替换身份、失败与异常、resume 内重新覆盖、调度拒绝和过期 epoch。
- 实际 timer 测试保留原周期 backlog 失败复现，并验证 Paused gameplay 抑制、completion 保留、one-shot 延后一次、取消/停止清理。同步/分阶段启动测试增加实例代次唯一性。
- 实际 System 显示来源/暂停接入测试验证覆盖→息屏→亮屏仍覆盖、末次解除和生命周期失败不困住 Quick Settings；原前台恢复测试增加 Paused 身份，正常 stop 测试验证产品原因复位。
- 泡泡纸 3 项测试执行实际 App/model/sound 方法：19 个原布局泡泡、多点/按下、重复帧、取消/松开不变成长按、840 ms 自动补充、暂停/新实例、迟到 timer、启动失败；音效静音/忙/stream 失败、borrowed 生命周期、尾部非阻塞释放、旧 release 与分配异常清理。
- Audio 原子空闲选择测试验证忙时没有 source/queue/HAL 副作用，默认原调用仍保留抢占语义；只改变明确 opt-in 的短音效调用。
- 两项默认 Python 缺少 littlefs 而跳过的测试，使用 v5 完整构建生成的 `littlefs_py_venv/bin/python` 分别补跑，均通过：内置 App 更新保留数据/重新验证、分区扩容保留私有文件/失效旧 Core seals。

- 最终 `python3 scripts/check.py` 全部通过；跨模块最后一组 186 tests、2 skipped；两项 skipped 已在上述 littlefs 环境补跑通过。各 Owner 的组件/App 测试组亦通过。日志：`/private/tmp/espocket-028-lifecycle-host-v4.log`。
- `python3 scripts/docs/check.py --markdown` 通过 353 份文档；Git whitespace 检查通过。
- 对照最终候选 staging，System/Shell/泡泡纸的 61 个生产 C++/header/JSON 文件与 checkout 字节一致；Core/Audio 原始 source inventory 与全部 patch SHA-256 复核通过；Core 两份 manifest 字节一致。

最终隔离完整构建 v5 成功（exit 0），候选目录 `/private/tmp/espocket-028-lifecycle-build-v5/candidate`，日志 `/private/tmp/espocket-028-lifecycle-build-v5.log`。使用已验证的 027 候选配置 `/private/tmp/espocket-027-candidate-v3/candidate/configuration/sdkconfig` 作为输入；归档内保留原始、准备后与最终配置。最终 App 固件 11,292,032 bytes（`0xac4d80`），最小 App 分区剩余约 23%。候选 114 项 artifact 的大小与 SHA-256 全部复核匹配，flash_files 均在归档 inventory 中。

- 输入 fingerprint：`319fba43c9d9fcd762985cdcde4b10a2e9bf6ef55da89083c7414fd03f311070`。
- `manifest.json` SHA-256：`2e27689562dc429c62a6c2e40b33c7ffec27f6c16218e782606486a619f1d948`。
- `espocket.bin` SHA-256：`a42f0ececc8db8a3165971da6658e58d0ddc2ebb1410b0ecaa799be542613272`。
- 最终 `configuration/sdkconfig` SHA-256：`fe9ede90d86c597d36f205b7679cc96241facfd193addd8a64b3eaeccd4940d2`。

归档声明 `deployed=false`、`physical_validation=false`；文件系统是 fresh filesystem，不能作为保留设备数据的迁移镜像。早期 v1 构建失败，v2–v4 在修正源码期间中断，均不作为交付候选。Host 边界替身不能证明真实 GUI 绘制、无线/触摸/音效/线程时延。

## 剩余门槛

[028/09](../issues/09-device-acceptance.md)仍待设备：下拉/覆盖/息屏的真实时序、取消/多点与长按手感、声音和颜色。音效输出不能以编译成功认定可听；防回音、声音卡顿和打断仍按原设备票验收。其余五个游戏、IMU、HID 和蓝牙遥控未由本批关闭。
