# USB Driver 设备验收与失败诊断

Date: 2026-10-02
Scope: 012/03 真实设备 synthetic-input；物理/视觉证据仍由各自 ticket 持有。

## 准备与身份

013 用户已确认旧镜像 e8bbe74ff 的集中 smoke「全部正常」，04/06 与 Spec 已关闭。设备清单标识 ESPocket-Waveshare-A0F262E30B68，由本次操作者登记，对应 USB Serial/JTAG serial_number A0:F2:62:E3:0B:68；不是串口路径作为唯一身份。

刷入前只读备份 LittleFS：首个 460800 attempt 在约 73% 出现 Serial data stream stopped，原日志保留；115200 独立重试完整读取 5,120,000 字节，保存 /private/tmp/espocket-pre-driver-littlefs-retry.bin。随后只写 App 0x60000 与 LittleFS 0xaa1000，两份 hash 均由 esptool 验证。未写 NVS、分区表或 bootloader。新镜像为 de1d41337，产物完整 hash 引用 [声明式 Card 记录](../../014-app-navigation-card-contract/records/2026-10-02-declarative-runtime-card.md)。

## 独立 attempts

- 20261002T082525Z-00dc03b6-0384-4db2-84d8-d6c8be8a2e59：FAIL。hello identity 与五项能力匹配；Watch Face/Launcher/Card/Quick Settings 首次路径通过，再次进入 Launcher 意外打开 Native Root。最终 release 成功，快照保留实际前台 Native Root；没有把 ACK 算成 PASS。
- gesture-repro-8895a410-0a48-41a3-8dee-7736f999068e：短路径 PASS，仅用于区分间歇现象，不代替整套设备验收。
- gesture-repro-124e8cc8-fdc5-489f-a3a0-1796f94b19fc：FAIL。快速路径在第一次 Launcher 下拉时捕获「A stack overflow in task espocket_test_u」，随后 RTC_SW_CPU_RST。release 与 snapshot 清理均超时，保留失败。不能归因于无证据的 USB 外部复位。

每个 report.json 与 serial.log 分别保存在 /private/tmp/espocket-device-attempts/<attempt>/，不覆盖既往结果。

## 修复与验证

实际 USB worker 原栈为 4096 字节；首次容量探针提高到 8192 字节内部栈，但启动时 task creation failed，hello 超时；镜像 5f8a1970b 与独立 attempt 20261002T083700Z-6432d4d7-bc92-4170-ba31-f3b255936bb4 保留。当前使用 ESP-IDF 已启用的外部栈能力，把 8192 字节分配至 PSRAM，并配对 xTaskCreateWithCaps/vTaskDeleteWithCaps，保留原 JSON 帧大小/命令/Owner 边界。Driver 增加直接识别 stack overflow 行，新的主机回归先失败再通过，避免等待 ROM banner 才识别失败。间歇 Launcher 误触仍需独立验证；不通过调整坐标隐藏问题。

以下最终结果补齐本轮构建、刷写和设备条件；新 Card 样例与 Native/Runtime 物理/视觉条件仍不据此勾选。

Xtensa 实际编译的静态栈帧为 run 448 字节、handle_line 1088 字节（未含调用链）；它们不等于任务峰值，不作为已证明 4 KiB 足够的依据。

PSRAM 栈镜像 c4e5f1c44 写入 hash 验证通过。attempt 20261002T084852Z-773a6ec1-3f0e-4d25-a298-9d4c665785a5 正常协商并通过表盘、Shell、Native Root/Detail、Edge Back 等路径，没有新的栈溢出；在 Back 确认等待处 FAIL，实际已回 Root。日志同时记录 Quick Settings 上滑回表盘后亮度从 68 变 84，显示消费手势仍可能生成按钮动作。下一修复在提交任何 GestureIntent 前，对 LVGL pointer 等待 release，防止切页将持有中的滑动变成新按钮 press；保持原 profile 坐标，不伪造导航状态。Native 参考确认开关增加状态日志用于区分真实切换。

## 最终结果

普通配置镜像 09e8eb00d 构建、App 分区写入与 hash 校验通过；Card/reclaim 测试开关关闭。44 项 host unittest、M2 parser、Markdown 均通过。

独立 attempt 20261002T085731Z-56520ddf-db93-42e4-844d-2ca468a28616：PASS，35 步全部通过。包含 Launcher/Card/Quick Settings、Native 子页 Back、Root 无 Back、确认/重复/取消/允许/15 秒超时/迟到确认、待决时 PWR Home、重开 Root/确认默认 Off，以及表盘息屏/唤醒。最终 release ok，seq 583，watch_face/display=true、前台 App/Page 为空、inputBusy=false。普通日志没有 panic、栈溢出或重启；亮度日志仅为初始唤醒 84、息屏 0、最终唤醒 84，Quick Settings 返回期间不再额外改动亮度。

源码修复分别为：USB task 用已启用的 ESP-IDF PSRAM 栈与配对释放 API，避免 4 KiB 峰值溢出且不新增 8 KiB 内部 SRAM 压力；Shell 在提交共享 GestureIntent 前让 LVGL pointer 等待 release，阻止同一次导航滑动生成按钮点击。没有修改 managed_components、profile 坐标、协议状态事实或 Navigator 栈。Native 参考 App 只增加确认切换状态日志。

没有留下临时 DEBUG 插桩。实际 Driver 作为回归 seam 已先捕获错误，再通过相同坐标和 Owner 快照；主机栈日志回归也先失败再通过。没有用浅层 mock 宣称验证了 LVGL 或 FreeRTOS 峰值。012/03 与 Spec resolved，所有报告仍标记 physicalInputVerified=false、visualVerified=false。

- 最终 espocket.bin SHA256：1960dd4f9e3838e4db9ea30a51321d8cf5c1dafc0a83c4aa7783e5bace22b244。

- 最终 espocket.elf SHA256：09e8eb00d868c6f21034ee25d1c9ce83d23457201dfc771ac5aad01ad790e582。

- 完整 LittleFS 备份 SHA256：5a1469ee24ca02b82078fd5b1a6a640e2e9f4d7f462e333e9ead99afb90d68aa。
