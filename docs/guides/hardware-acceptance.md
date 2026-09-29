# 真机验收执行清单

> 文档类型：操作指南。阶段门槛和状态仍以对应 acceptance 文档为准。

本清单供拿到 Waveshare ESP32-S3-Touch-AMOLED-1.75C 后执行。它整理 [M4](../milestones/m4/acceptance.md)、[M6](../milestones/m6/acceptance.md)、[M7](../milestones/m7/acceptance.md) 和 [M8](../milestones/m8/acceptance.md) 的既定门槛，不改变阶段依赖、固定次数或 PASS 判定。当前清单中的真机项目均未因本文而通过。

## 出发前准备

1. 选定同一个待验收提交，确认工作区、`firmware/dependencies.lock`、板型和 ESP-IDF 6.0.1。记录提交 ID、`espocket.bin` 与 `littlefs_data.bin` 的 SHA-256，以及 `CONFIG_ESPOCKET_M6_SCREEN_TIMEOUT_SECONDS` 的值。默认超时为 30 秒，`0` 表示 Never。
2. 准备固件、LittleFS 镜像、刷写命令、串口终端和对应 ELF。刷写后记录设备启动 banner、固件版本和镜像哈希；确认实际运行的是待验收版本。旧版真机证据不能替代新版观察。
3. 复制[原始记录模板](hardware-acceptance-record-template.md)到 `docs/milestones/evidence/m6/` 或 `docs/milestones/evidence/m7-m8/` 下以阶段、场景、日期命名的**新文件**，同时保留完整脱敏串口记录。已被验收文档引用的证据文件不可覆盖。
4. 先确定回收和无效来源测试的可控触发方式。当前产品代码没有默认关闭的“息屏期间回收前台 App”或“使 Launch Source 失效”测试入口；在入口可用且能证明目标确实失效之前，M6 的回收 fallback、M8 的 Native/Runtime 回收与无效来源项保持 `NOT TESTED`。不得把正常 Home 后停止 App 当作息屏期间回收。
5. M5 在线 Store Refresh 已有真机崩溃证据；本轮 M6–M8 验收不主动执行该路径，避免故障混入导航和生命周期记录。

每个固定循环在开始前标记 attempt 编号，记录屏幕实际显示、触摸或按键操作、串口对应时间，以及 PASS/FAIL。出现失败时保留原样并停止宣称该项通过；不能增加成功次数抵消失败。串口记录须移除 SSID、凭据、私钥和其他敏感值。

## 第一站：M6 Home 与显示状态

先执行 [M6 Hardware Acceptance](../milestones/m6/acceptance.md#hardware-acceptance) 中的四条固定路径，每条**恰好 5 次**：

| 路径 | 每次要观察的关键点 |
|---|---|
| 冷启动 → Watch Face | 首个 Home 是表盘；时间未同步时占位合理；上滑能到固定 Launcher |
| App → PWR Home → Watch Face → PWR Off → PWR Wake | 每次短按只推进一个预期状态；App 停止后不遗留 Overlay |
| App Detail → 自动息屏 → PWR → 恢复 App | 息屏前后同一可见页面与导航位置；息屏期间触摸没有执行页面动作 |
| App 在息屏期间被回收 → PWR → Watch Face | 先证明 App 已失效；唤醒不自动重启或显示失效页面 |

再分别检查一次：息屏触摸、键盘或其他临时 Overlay 上的 PWR、BOOT 无日常导航动作、PWR 长按仅有硬件开关机语义，以及全程无 panic、watchdog、assert、死锁或持续资源下降。M6 的显示与触摸结果必须有物理观察；日志只作对应证据。缺任一必须项，M6 保持 `IN PROGRESS`，不进入 M7 正式验收。

## 同机补测：M4 未完成的设备页面

在不影响 M6 固定循环的独立窗口中，打开官方 Settings，单独记录 Storage 可见信息和 Developer/debug 控件的实际显示与操作结果。保留对应串口和屏幕观察。Sound/Volume 仍依赖上游 playback-only 能力修复；这两项通过也不会单独使 M4 `PASS`。

## 第二站：M7 系统导航

仅在 M6 `PASS` 后执行 [M7 Hardware Acceptance](../milestones/m7/acceptance.md#hardware-acceptance)：

1. 完整导航闭环执行 **5 次**：Watch Face → Card 边界 → Battery → Brightness 操作 → Watch Face → Quick Settings → Settings → Back → Quick Settings → Back → Watch Face → Launcher → Native Root → Detail → Back → Root → Back → Launcher → PWR → Watch Face。
2. Wi-Fi 真实切换和 Brightness 真实变化各记录 **5 次**；不能仅记录控件文案。
3. 单独覆盖 Card → App → 原 Card、Watch Face Edge Back 无动作、App 普通横滑不误触发 Back、任意非 Home Surface 的 PWR Home，以及 [M7 表格](../milestones/m7/acceptance.md#required-path-coverage)中的其他路径和故障扫描。

若某次失败，保留失败并调查，M7 不标记 `PASS`；M8 仍保持 `NOT ENTERED`。

## 第三站：M8 Native 与 Runtime 契约

仅在 M7 `PASS` 后执行 [M8 Hardware Acceptance](../milestones/m8/acceptance.md#hardware-acceptance)。使用真正的 Hello Native 与 Hello Runtime；Runtime 不能用 Native mock 代替。

- Native 与 Runtime 各执行 **5 次** Root → Detail → Back → Root → Back → Launch Source → PWR Home。
- Native 与 Runtime 各执行 **5 次** 后台回收 → 重新启动，证明从 Root 开始且旧页面与临时 Overlay 不可恢复。
- 分别检查两种 App 的息屏／唤醒、普通横滑、无效 Launch Source fallback，完成生命周期、heap 和故障扫描。原始记录中标明执行模型、attempt、来源及最终目标。

M8 的 Runtime 验收还依赖真实 Runtime App 路径；M3 已 `PASS` 不替代上述新证据。

## 收尾

只把真实完成且证据齐全的项目从 `NOT TESTED` 更新为结果，失败项保留失败。按 M6 → M7 → M8 的阶段顺序更新各验收文档和总览，并附上新证据路径、固件哈希和具体结论。M4/M5 的独立 blocker 不因 M6–M8 完成而自动解除。
