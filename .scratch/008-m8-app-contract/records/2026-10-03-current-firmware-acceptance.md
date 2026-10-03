# 2026-10-03 — 当前音频修正固件的 App 验收

用户要求先验证剩余条件，减少重复人工操作。当前无测试音 Audio candidate hello `b9b4a413f`；未切换镜像或写入数据分区。

## 自动路径

一次完整 apps 套件 PASS，共 57 步；attempt `20261003T104128Z-f674a477-0034-4e9e-85e1-b0a772566363`。覆盖真实 Native/Runtime Root、Detail、普通横滑、Edge Back、确认开启、重复 Back、取消/允许/超时、PWR Home、重新启动 Root 及未回收息屏恢复。日志未匹配 panic、stack canary、watchdog、assert 或 Fatal initialization failure。此扫描不证明所有错误均不存在，也不关闭 Audio teardown 告警。

报告 `/private/tmp/espocket-audio-clean-app-acceptance/20261003T104128Z-f674a477-0034-4e9e-85e1-b0a772566363/report.json`；最终 release=ok，watch_face/display=true，foregroundAppId/pageId 为空，backPending/inputBusy=false。合成输入不代替画面、真实触摸或 GPIO 验收，不重复已经接受的 Native 常规人工路径。

## 人工路径

已请求一次 Runtime 集中物理检查：Root 无 Back、普通横滑保留 Detail、Confirm Back On 的可见反馈、pending/Cancel、自动息屏后实体 PWR 恢复 Detail、Allow 回 Root、PWR Home。结果待用户；监听日志 `/private/tmp/espocket-runtime-physical-20261003.log` 有限 600 秒，窗口结束后不能声称捕获了之后操作。

Native-only/Runtime-only 回收物理条件与 Settings Storage/Debug、Launcher 手感仍未完成；不以本次普通固件 apps PASS 替代。
