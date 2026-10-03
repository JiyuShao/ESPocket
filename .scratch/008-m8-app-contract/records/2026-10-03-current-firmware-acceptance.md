# 2026-10-03 — 当前音频修正固件的 App 验收

用户要求先验证剩余条件，减少重复人工操作。当前无测试音 Audio candidate hello `b9b4a413f`；未切换镜像或写入数据分区。

## 自动路径

一次完整 apps 套件 PASS，共 57 步；attempt `20261003T104128Z-f674a477-0034-4e9e-85e1-b0a772566363`。覆盖真实 Native/Runtime Root、Detail、普通横滑、Edge Back、确认开启、重复 Back、取消/允许/超时、PWR Home、重新启动 Root 及未回收息屏恢复。日志未匹配 panic、stack canary、watchdog、assert 或 Fatal initialization failure。此扫描不证明所有错误均不存在，也不关闭 Audio teardown 告警。

报告 `/private/tmp/espocket-audio-clean-app-acceptance/20261003T104128Z-f674a477-0034-4e9e-85e1-b0a772566363/report.json`；最终 release=ok，watch_face/display=true，foregroundAppId/pageId 为空，backPending/inputBusy=false。合成输入不代替画面、真实触摸或 GPIO 验收，不重复已经接受的 Native 常规人工路径。

## 人工路径

已请求一次 Runtime 集中物理检查：Root 无 Back、普通横滑保留 Detail、Confirm Back On 的可见反馈、pending/Cancel、自动息屏后实体 PWR 恢复 Detail、Allow 回 Root、PWR Home。结果待用户；监听日志 `/private/tmp/espocket-runtime-physical-20261003.log` 有限 600 秒，窗口结束后不能声称捕获了之后操作。

Native-only/Runtime-only 回收物理条件与 Settings Storage/Debug、Launcher 手感仍未完成；不以本次普通固件 apps PASS 替代。

## Runtime 物理结果

用户对上述一次集中操作回复“全部正常”：Root 无 Back、普通横滑保持 Detail、Confirm On/pending/Cancel 的可见反馈、自动息屏后实体 PWR 恢复 Detail、Allow 回 Root、PWR Home 均通过。此为用户直接物理/视觉观察，不能等同于串口完整采集：600 秒监听已结束，日志仅有息屏输出，未抓到本次完整人工步骤。对应自动 57 步记录独立保留。

随后进入既有 Native-only/Runtime-only 回收镜像的单次人工验收；它们是保存的专用旧镜像，不包含本次 Audio/Settings 候选，不用来宣称当前普通固件开启回收。完成后恢复 `b9b4a413f`。

Native-only 保存镜像重新核对 ELF/BIN hash 与单独回收配置后，App-only 写入校验 PASS，启动 PASS，hello 精确匹配 `01a86838e`；初始 snapshot 为表盘亮屏、无 App/Page/pending/inputBusy。日志 `/private/tmp/espocket-native-reclaim-physical-flash.log`、`boot.log` 与 `capture.log`（后二者同 physical 前缀）。已请求一次 Native 确认提示 → Cancel → 自动息屏回收 → PWR 表盘 → 重开 Root 的物理检查，结果待用户；当前设备为该专用测试镜像。

## Native 回收物理结果

用户对一次 Native 确认 On/pending/Cancel → 自动息屏回收 → 实体 PWR 表盘 → 重开 Root 的集中检查回复“全部正常”。Native 待决返回反馈与回收后的物理恢复条件通过；依据为用户直接观察，串口窗口实际覆盖情况独立核对。旧镜像只证明这一已构建回收配置的路径，不代表普通 Audio 修正镜像开启回收。

本次 Native 监听覆盖到实际 `APP_RECLAIM_TEST stopped model=native manifest=espocket.app.hello app_id=1` 及 Off/On/Wake；未匹配 Guru Meditation、Stack canary 或 assert failed。用户回复后主动终止只读监听，退出 130 为采集进程中断，不是设备崩溃。物理画面判定仍以用户反馈为准。

Runtime-only 保存镜像 ELF/BIN 与回收配置核对通过，App-only 写入 hash 校验及启动 PASS；hello 精确匹配 `439f6431a`，初始为表盘亮屏、无 App/Page/pending/inputBusy。日志 `/private/tmp/espocket-runtime-reclaim-physical-flash.log`、`boot.log`、`capture.log`（后二者同 physical 前缀）。Runtime 自动息屏 → 实体 PWR 表盘 → 重开 Root 的一次物理观察待用户；当前设备为专用 Runtime 回收镜像。

## Runtime 回收回应与采集差异

用户对 Runtime 回收步骤回复“是的”。但复核有限 600 秒采集窗口：Runtime 启动后约 1.3 秒有实体 PWR 并 stop 回表盘，之后进入 Native Detail；窗口内没有 `APP_RECLAIM_TEST stopped model=runtime`。不能将该日志写成 Runtime 自动回收通过。已请求确认是否在采集窗口结束后完整执行 Runtime Detail → 自动息屏 → PWR 表盘 → 重开 Runtime Root；答复前该物理条件保持 pending。

Runtime 回收镜像原有 17 步自动 PASS 继续有效，不能替代本次尚待澄清的物理结果。恢复无 fixture 普通 Audio 修正镜像已经开始，实际恢复结果待补录。

## 普通镜像恢复

`b9b4a413f` 无测试音、关闭两种回收测试的 Audio 修正普通镜像已恢复，App-only 写入 hash 校验 PASS、启动 PASS。`/private/tmp/espocket-app-acceptance-final-state.json` 精确 hello 核对后 release=ok，最终 seq=1、watch_face/display=true，App/Page 为空、canBack/backPending/inputBusy=false。原始 flash/boot/state 日志同 `/private/tmp/espocket-app-acceptance-final-` 前缀。数据分区未刷写，无监听进程遗留。

普通 Runtime 与 Native 回收物理条件已接受；Runtime 回收的回应与窗口内操作不一致，仍等澄清，008/03、008/04 不提前关闭。
