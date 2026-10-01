# M6 Native Detail 真机复测（2026-09-29）

此前真机发现 Hello Native 的 **Open Detail** 按钮可见但点击无反应。`hello_app.cpp` 的 JSON 声明了点击动作和 `root → detail` 页面流转换，但 `HelloApp` 只订阅了计数动作。修复后 App 订阅 `hello.open_detail`，收到事件时显式触发 `main` 页面的 `open_detail` 转换；未修改 Brookesia managed components。

新 App 镜像 SHA-256 为 `741f2ab0c8817aea69ee0fba04d417b1313daf4eb48c77b34a9913f52cc4124d`。隔离构建成功，esptool 只刷写 App 分区 `0x60000` 并报告 `Hash of data verified`，NVS 和 LittleFS 未擦写。

| 场景 | 实机观察 | 串口证据 |
|---|---|---|
| Native Root → Detail | 用户确认显示 `Native Detail` | `flow(main), from(root), action(open_detail), to(detail)` |
| Launcher → Watch Face | 用户确认从屏幕边缘向内横滑可返回；短按 PWR 也可返回 | 此次边缘手势确认依赖物理观察；此前串口记录过 PWR Home 转换 |
| Detail → 自动息屏 → PWR 唤醒 | 用户确认约 30 秒自动息屏，并恢复到同一个 `Native Detail` 页面 | 本次串口记录了 Detail 状态与 `M6 display state: Off`；采集在唤醒前结束，未捕获 Wake 日志 |

关键串口时间戳：`67011 ms` 为 `root → detail`，`96995 ms` 背光降至 0，`97012 ms` 记录 `M6 display state: Off`。原始串口日志保存在本地 `/private/tmp/espocket-detail-serial-20260929.txt`，不纳入源码树。自动恢复是一轮有效的物理冒烟观察，但缺少对应 Wake 串口记录，暂不计入 M6 固定 5 次正式验收。后续验收需要让串口贯穿完整的 Detail → Off → Wake 循环。
