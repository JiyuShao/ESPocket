# 03 — 完成 Home 与显示真机验收

**What to build:** 为固定 Home、PWR、Screen Off、resume 与 fallback path 取得真机 evidence。

**Blocked by:** 02 — 增加可控 reclaim fallback seam。

**Status:** resolved

- [x] 四条必需路径各自恰好通过 5 次。
- [x] Touch-off、Overlay、BOOT 与 long-press 检查通过。
- [x] 串口与物理观察中无 fatal signal。

## 验收过程

2026-10-01：四条固定路径和四项单项检查已通过；普通镜像离线 Store 停留约 110 秒并用 PWR 退出，未见 fatal signal。见 [M6 验收](03-run-hardware-acceptance.md)及[Store 定向复测](../records/2026-10-01-store-failure-rescan.md)。当时尚缺跨重复操作的资源趋势证据。在线 Store 稳定性归 M5，不是本 ticket 的关闭条件。

## Resolution

2026-10-02：用户完成 10 轮 Native Detail → PWR Home/Off/Wake，屏幕顺序均正确；同状态资源诊断在第 2、4、7、8、10 检查点采到四项指标，首末变化为 `0 / +28 / 0 / 0 B`，无持续下降或 fatal signal。诊断后已刷回普通镜像并确认表盘正常。见[资源趋势记录](../records/2026-10-02-resource-trend.md)。M6 全部门槛通过。

## 真机步骤与已接受结果

本票要求真机证据；Preview、host 测试或日志不能替代物理显示、按键和触摸观察。

### Fixed repetition counts

以下次数均为固定验收要求，且不超过 5 次。任何一次失败都必须记录，不能通过追加成功次数稀释。

| 路径 | 次数 | PASS 条件 | 状态 |
|---|---:|---|---|
| Cold boot → Watch Face | 5 | 每次都显示 Watch Face，无 Launcher 先成为 Home | 5/5 PASS（2026-10-01；[逐次记录](../records/2026-10-01-cold-boot.md)） |
| App → PWR Home → Watch Face → PWR Off → PWR Wake | 5 | 顺序和可见状态均正确 | 5/5 PASS（2026-10-01，普通镜像；[逐次记录](../records/2026-10-01-pwr-sequence-followup.md)） |
| App → Auto Screen Off → PWR → Resume App | 5 | 恢复同一可见页面及导航位置 | 5/5 PASS（2026-10-01，普通镜像 Native Detail；[记录](../records/2026-10-01-reclaim-test-image.md)） |
| Resume target reclaimed → PWR → Watch Face | 5 | 不自动重启 App，不出现空白或失效页面 | 5/5 PASS（2026-10-01，测试镜像；[记录](../records/2026-10-01-reclaim-test-image.md)） |

### Required one-pass checks

| 检查项 | PASS 条件 | 状态 |
|---|---|---|
| Screen Off touch | 触摸不触发当前页面操作 | PASS（2026-10-01，Native Detail；[记录](../records/2026-10-01-one-pass-checks.md)） |
| Overlay + PWR | 临时 Overlay 存在时仍回 Watch Face，可放弃未提交输入 | PASS（2026-10-01，Settings 密码键盘；[记录](../records/2026-10-01-one-pass-checks.md)） |
| BOOT | 不触发 Back、Home、Shortcut 或 Recent Apps | PASS（2026-10-01，两键对照；[记录](../records/2026-10-01-one-pass-checks.md)） |
| PWR long press | 仅表现为硬件固定开机/关机 | PASS（2026-10-01，硬件关机及 PWR 重新上电；[记录](../records/2026-10-01-one-pass-checks.md)） |
| Failure scan | 无 panic、watchdog、assert、deadlock、错误触摸执行或持续性资源下降 | PASS（2026-10-02）：固定路径和单项检查无 fatal signal；同状态资源样本覆盖第 2–10 检查点、四项未持续下降；离线 Store 定向复测未复现旧栈溢出（[资源记录](../records/2026-10-02-resource-trend.md)、[Store 复测](../records/2026-10-01-store-failure-rescan.md)） |

## 证据规则与测试镜像

- 每次固定循环必须能区分 attempt 编号与结果。
- 串口证据必须与物理观察对应；只打印目标状态不证明屏幕已正确显示。
- App 回收可以使用明确的测试入口模拟，不要求先实现通用资源管理器。
- 页面身份与导航位置需要恢复；输入焦点、键盘、弹窗和进行中的触摸不属于恢复保证。
- 任一必需项缺少证据时不得关闭本票。

### Reclaim fallback 测试镜像

仅用于 `Resume target reclaimed` 路径。`firmware/sdkconfig.defaults.m6-reclaim` 开启 `CONFIG_ESPOCKET_M6_RECLAIM_ON_TIMEOUT_TEST`；普通固件默认关闭。测试镜像在 App 自动息屏后经 System Core 停止该 App，保留失效的 resume target，随后用 PWR Wake 验证表盘回退。该入口不模拟通用内存管理器。

```bash
source "$HOME/.espressif/v6.0.1/esp-idf/export.sh"
RECLAIM_BUILD="$PWD/firmware/build/m6-reclaim"
idf.py -C firmware -B "$RECLAIM_BUILD" -D SDKCONFIG="$RECLAIM_BUILD/sdkconfig" \
  -D 'SDKCONFIG_DEFAULTS=components/gen_bmgr_codes/board_manager.defaults;sdkconfig.defaults;sdkconfig.defaults.m6-reclaim' build
```

验收时需记录镜像 hash、`M6_RECLAIM_TEST` 串口事件和每次屏幕实见结果；普通 App 自动息屏恢复路径仍使用关闭该开关的候选镜像。

### 资源趋势诊断镜像

`firmware/sdkconfig.defaults.m6-resource` 开启默认关闭的 `CONFIG_ESPOCKET_M6_RESOURCE_TRACE`。它仅在表盘亮屏、PWR 即将息屏时打印同状态 internal/PSRAM free 与 largest block。独立构建、App 分区刷写、真机循环、采样限制与普通镜像恢复见[资源趋势记录](../records/2026-10-02-resource-trend.md)。诊断镜像不作为普通固件交付。
