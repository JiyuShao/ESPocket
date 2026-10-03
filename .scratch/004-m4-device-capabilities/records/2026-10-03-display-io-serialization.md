# 2026-10-03 — Display 背光与刷屏 IO 串行化候选

## 最小失败与归属

用户更正：只左右来回拖 Settings → Display 亮度滑块即可概率卡死，主题与 Later 不必要。旧镜像 `ac2485543` 在恢复后只拖滑块的自动路径中，第 60 次出现实际 `Display:SetBacklightBrightness wait timeout`（500ms），随后快照 response timeout；此前 59 次均命中 HAL brightness Owner。脚本 `/private/tmp/espocket_brightness_only.py`，日志 `/private/tmp/espocket-brightness-only-baseline-serial.log` 与结果 `/private/tmp/espocket-brightness-only-controlled-result.log`。不是坐标未命中或 theme 特有故障。

第一次卡死现场的 JTAG 调用栈：SvcMgrMain1 在 CustomDisplayBacklightImpl::set_brightness_internal → esp_lcd_panel_io_tx_param → spi_device_acquire_bus 等待 SPI 总线；LVGL 在 Display::present_frame_sync 等待 Display mutex；touch task 也等待该 mutex，System 任务等 GUI 同步请求。OpenOCD 连接时因启用内存保护触发了工具自动软复位，保留了 TCB 栈记录，但不把它宣称为完全无扰动的现场；后续主要失败证据是未使用 JTAG 的纯滑块循环。调试连接已 resume/shutdown，未保留暂停状态。

Display 0.8.2 的刷屏方法在 output.draw_mutex 下、Display mutex 外进入 HAL；背光方法在 Display mutex 下进入同一 LCD 的 HAL command IO，却不取 output.draw_mutex。两个任务可以同时访问同一个 SPI Device。[ESP-IDF v6.0.1 官方说明](https://docs.espressif.com/projects/esp-idf/en/v6.0.1/esp32s3/api-reference/peripherals/spi_master.html#driver-features)要求多任务共享同一 SPI Device 时自行互斥，SPI bus acquire 不代替这个设备互斥。实际方法主机回归在暂停一次 frame IO 后启动 brightness，稳定发现 IO overlap；错误断言为 `brightness/power must not overlap an in-progress frame on the same LCD IO`。

## 候选修正

在真实 Owner Display 0.8.2 维护补丁，运行时 set brightness/on-off、load/reset data 按同一输出 draw_mutex 串行化；顺序与 frame submission 一致：获取输出锁引用时短暂取状态锁并释放 → 输出锁 → 状态锁。事件与持久化在两把锁之外执行。保留旧状态回滚、output 消失检查和原始 Service API，不让 Settings 私下访问 HAL，不创建第二套 Display 状态。

补丁、完整源 inventory/hash、上游版本 commit 和移除条件放在 `firmware/patches/espressif__brookesia_service_display/0.8.2/`。原始 managed_components 未改。新 `display-candidate` 构建组合继承已验收 audio-candidate 配置，加上此补丁，默认 production 清单不变；上游报告尚未提交。

## 测试与限制

`firmware/test/host/test_display_io_serialization.py` 提取并执行实际 Display frame/backlight 方法，只替换 HAL/Storage sink。旧源码必须出现 IO overlap，候选覆盖 brightness、power、load、reset，另检查等待输出锁时状态锁仍可获取；主机通过。人工听感、触摸硬件和像素不由此测试证明。

设备回归入口新增 `settings-brightness`：同一 Display 页面左右交替拖动，每次必须有真实 HAL brightness 日志，任何服务 timeout 立即失败，末尾实际合成 Back 与 Home 必须工作；默认当前 profile 为 100 次，针对旧固件第 60 次才失败的概率缺陷。该数量只用于自动压力回归，不增加人工操作次数。

完整候选构建与同一路径自动设备结果见下文；004/08 仅保留必要实体触摸观察，不把合成输入算作物理验收。

## 候选构建与设备结果

完整 display-candidate 构建通过；原始 registry lock 与 playback-only SDK 配置验证通过，原候选配置的内存保护未因 JTAG 取证被关闭。候选 identity `e15f52712`，ELF SHA256 `e15f52712bbbfb0d429e5906a0f8b78bed416f0863fb9498341222231edca106`；BIN SHA256 `554b92bb9787177c5409528f4328010316773e682850786a759c51271d0ec48d`。仅写 App 0x60000 并校验，未覆盖 NVS 或 Runtime 文件系统；正常启动、恢复 Dark。

主机统一检查通过（firmware/test/host 64 个测试及组件检查）；Markdown 检查通过。首次检查仅有 CLI help 的旧 suite 列表断言失败，更新增加的 settings-brightness 后通过，没有跳过该门槛。

自动套件 settings-brightness 完成 100 次，每次有实际 HAL brightness Owner 调用；没有亮度服务 timeout。末尾实际合成 Back 到 Settings Root、PWR Home 回表盘通过；release 成功，最终 display=true、watch_face、无前台 App、inputBusy=false。

自动设备报告：`/private/tmp/espocket-display-lock-device/20261003T150518Z-448dd3a6-3cd0-4c0f-ac59-0274cc47a46b/report.json`（输入类型 synthetic-input；physicalInputVerified=false、visualVerified=false）。当前候选已刷入并停在表盘。相比旧固件第 60 次卡死，原最小硬件驱动路径的新 100 次全部通过；不宣称任意压力下永不失败。实体触摸仅待一次有限观察，不增加人工多轮测试。

没有新增固件 debug 探针或关闭内存保护；原始依赖源码未改，上游提交仍未进行。

## 实体验收

2026-10-03：用户在当前候选 e15f52712 上确认“确实没问题了”。004/08 的唯一剩余实体触摸门槛通过，票据关闭。此项用户观察独立于上述 synthetic-input 报告，未更改其 physicalInputVerified=false / visualVerified=false。默认 production 合入和其他视觉票据仍按各自门槛执行。
