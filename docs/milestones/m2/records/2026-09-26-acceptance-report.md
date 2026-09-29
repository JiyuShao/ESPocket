# M2 验收报告

> 文档类型：历史验收记录。2026-09-29 迁移到 `records/`；原有日期、状态、结果、失败、豁免和证据 identity 保持不变。当前阶段判定见 `../acceptance.md`。

## 状态

- Source/build implementation: `PASS`
- M2: `PASS`（2026-09-26）
- M1: `PASS`（2026-09-25，`v0.1-system`）
- M0: `WAIVED`（2026-09-25，非 PASS）

M2 的设备端 50-cycle lifecycle/heap gate 与 normal image 真机 Launcher/Hello/Increment/Home 可视交互均于 2026-09-26 通过。

## Scope

- 新增真实、可见的 `HelloApp` Native `IApp`：`Hello ESPocket`、counter、Increment。
- `espocket::System` 显式安装 Hello 与隐藏 Circular Shell；不启用 Provider auto-install。
- Circular Shell Launcher 启动 stable manifest ID `espocket.app.hello`。
- persistent `SystemTop` Overlay 的 bottom Home gesture 停止当前可见 active app，并重新挂载 Launcher。
- 删除 M1 临时 `TestPage`。
- 默认关闭的设备端 50-cycle lifecycle stress path；Host 仅解析串口。

## Build

| 项目 | 结果 | 状态 |
|---|---|---|
| ESP-IDF / target | 6.0.1 / ESP32-S3 | PASS |
| Locked Brookesia baseline | `firmware/dependencies.lock`，System Core 0.8.4 | PASS |
| Previous normal firmware build | `idf.py -C firmware build`；在最终 Home concurrency remediation 前生成 | SUPERSEDED |
| Previous normal image | `0x4993a0` / 4,821,920 bytes；SHA-256 `ca94e3a47d8c560176cd354c25b7c345eb99a2cbe35459d4013359d7da16c447` | SUPERSEDED — DO NOT FLASH |
| Previous stress firmware build | 隔离 `SDKCONFIG` / build 目录；在最终 Home concurrency remediation 前生成 | SUPERSEDED |
| Previous stress image | `0x49a470` / 4,826,224 bytes；SHA-256 `a931eb4b08526a36920c719065ca126f9266f1a3cd2eae01b8d412879e26e561` | SUPERSEDED — DO NOT FLASH |
| Current normal firmware build | ESP-IDF 6.0.1；全新隔离 build / generated SDKCONFIG；包含最终 M2 Home remediation 及 M3 Runtime JS | PASS |
| Current normal image | `0x514ce0` / 5,328,096 bytes；SHA-256 `89b42a51d0067c3530f469c3c1fd5d96f72d9f1ac15cae69deac306a0cb62ffe` | PASS, FLASHED 2026-09-26 |
| Current stress firmware build | 同一最终源码；全新隔离 build / generated SDKCONFIG；`CONFIG_ESPOCKET_M2_LIFECYCLE_STRESS=1`；map 保留 stress runner | PASS |
| Current stress image | `0x515d90` / 5,332,368 bytes；SHA-256 `8f7a8236d39ab9133588840a97817dd36f4d8bf735f49ca45e05f0ce40c60566` | PASS, FLASHED 2026-09-26 |
| Current LittleFS image | 5,120,000 bytes；SHA-256 `6fb5d2051b778957ec15a087f66b3455a8ffbf2ff9e6b0437b978734678624b0` | PASS, FLASHED 2026-09-26 |
| Embedded JSON parse | Circular Shell 与 Hello JSON 均通过标准 parser | PASS |
| Host verifier self-test | happy path、显式失败、median leak、5-sample 下降、零指标、cycle/marker 乱序、重复 run、run 前后孤立 cycle、畸形额外协议记录、GUI cleanup warning、正常 `task_wdt` debug 文本、run 内 ESP32-S3 reset reason；普通与 `python -O` | PASS |

## Native Lifecycle Design Evidence

| 检查项 | 实现 | 状态 |
|---|---|---|
| Install | `System::on_init()` 直接 `install_app(std::make_shared<HelloApp>())` | IMPLEMENTED |
| Registration/discovery identity | stable manifest ID `espocket.app.hello`；visible Native App | IMPLEMENTED |
| Start | Launcher 通过 `SystemApi::list_apps()` 精确匹配 ID 后 `start_app()` | IMPLEMENTED |
| Running | stress runner 每轮调用 `get_app()` 要求 `AppState::Running` | IMPLEMENTED |
| Interaction | `hello.increment` no-handler action → `on_action()` → `set_text()` | IMPLEMENTED |
| Stop | Display callback 不引用 Shell 实例，也不调用 Core：`Press` 快照 lifecycle generation token，首次越阈值后用 atomic latch 只发布一次 intent；Shell-owned 50 ms timer 在 Core app task 内消费 intent，重新核对 generation、tracked AppId 与 Core active app 后同步 `stop_app()` | IMPLEMENTED |
| Stopped | stress runner 每轮调用 `get_app()` 要求 `AppState::Stopped` | IMPLEMENTED |
| Launcher restoration | ESPocket System 在 `on_app_stopped()` / start-stop failure hook 中清理匹配的 foreground generation，并统一触发 Shell Launcher self-transition；若 Core 已有另一可见 active app 则不覆盖。System stop 先关闭 intent gate，再同步停止 Shell 与 foreground app；shutdown 期间的新 start 由 Core 回滚 | IMPLEMENTED |
| Core cleanup | `preload_dom=false`；每轮 stop 后调用公开 `gui_set_text()` 负向探针，只有精确返回 `App GUI document is not loaded` 才记录 `gui=Unloaded`；Core cleanup/unload warning 由 Host verifier 判为失败 | IMPLEMENTED |
| Shell callback cleanup | Home slot 只捕获 immutable provider 与 shared atomic gesture state；Shell stop 先断开 slot、停止 Core-owned Home timer，再释放 state。Wi-Fi/Battery/SNTP slot 共享 callback token，stop 断开后清空 owner 并等待在途回调退出 | IMPLEMENTED |
| App cleanup | Hello 不持有 context、timer、task、handler connection 或 service binding | IMPLEMENTED |

## Hardware Smoke

物理观察不得仅凭串口日志判定 PASS。

| 检查项 | 状态 | 备注 |
|---|---|---|
| Boot reaches Launcher | PASS | 用户于 2026-09-26 在 restored normal image 上确认 |
| Launcher shows `Hello Native` | PASS | 用户于 2026-09-26 确认 |
| Tap opens `Hello ESPocket` | PASS | 用户于 2026-09-26 确认 |
| Increment updates counter | PASS | 用户于 2026-09-26 确认 |
| Bottom Home stops Hello | PASS | 用户于 2026-09-26 确认 |
| Launcher is visibly restored | PASS | 用户于 2026-09-26 确认 |
| Home on Launcher remains no-op | PASS | 用户于 2026-09-26 确认 |

## 50-cycle Lifecycle Stress

### Build profile

- Kconfig: `CONFIG_ESPOCKET_M2_LIFECYCLE_STRESS`，default `n`。
- Checked-in overlay: `firmware/sdkconfig.defaults.m2-stress`。
- Stress profile must use an isolated generated `SDKCONFIG` and build directory; it must never overwrite the normal generated `firmware/sdkconfig`.
- Runner executes 50 real `System::start_app()` / `System::stop_app()` pairs before starting Circular Shell, then continues to the normal Launcher.
- Each marker explicitly records `start=Running stop=Stopped gui=Unloaded` and four nonzero raw heap metrics.

### Acceptance gates

1. Exactly one valid `BEGIN` / `COMPLETE` / final startup marker set; exactly ordered cycles `1..50`; any extra malformed protocol record, duplicate, omission, or concatenated attempt fails.
2. Every cycle reaches `Running`, then `Stopped`, then proves the non-preloaded Hello GUI document is unavailable as `gui=Unloaded`.
3. No `M2_STRESS FAIL`, Core GUI cleanup/unload warning, run-local boot-ROM reset record, panic, concrete ESP-IDF task/interrupt WDT failure, assert, abort, stack smashing, or heap-corruption signature；普通 `task_wdt` debug tag 本身不是失败。
4. Cycle 1 is warm-up and excluded from trend analysis.
5. Compare stopped-state medians for cycles 2–6 and 46–50:
   - internal free loss ≤ 1024 bytes
   - PSRAM free loss ≤ 1024 bytes
   - internal largest block loss ≤ 1024 bytes
   - PSRAM largest block loss ≤ 1024 bytes
6. Across cycles 2–50, no metric may strictly decrease over any five consecutive samples.
7. `M2_STRESS COMPLETE cycles=50` and final `ESPocket started` must both appear.

### Device result

`PASS`（2026-09-26）

- 用户明确授权在 `/dev/cu.usbmodem2101` 先写 stress、后恢复 normal，且不得擦除整片 Flash 或 NVS。
- Stress image 的 bootloader、partition table、app 和 `littlefs_data` 均由 esptool 写入并通过哈希校验；未执行 erase-all 或 NVS 擦除。
- Marker cardinality：BEGIN `1`；CYCLE `50`；COMPLETE `1`；`ESPocket started` `1`；cycles 精确为 `1..50`。
- 每轮均为 `start=Running stop=Stopped gui=Unloaded`；无 `M2_STRESS FAIL`、panic、assert、heap corruption、watchdog failure、run-local reset 或 Core GUI cleanup warning。
- cycles 2–6 对比 46–50 的 stopped-state median：

| Metric | Early | Late | Loss | Gate |
|---|---:|---:|---:|---:|
| internal free | 96,227 | 96,315 | 0 | ≤ 1,024 |
| PSRAM free | 4,183,640 | 4,184,372 | 0 | ≤ 1,024 |
| internal largest | 31,744 | 31,744 | 0 | ≤ 1,024 |
| PSRAM largest | 4,128,768 | 4,128,768 | 0 | ≤ 1,024 |

- verifier 同时确认 cycles 2–50 的所有指标均未跨五个连续样本严格下降。
- 验证完成后，normal image 已按同一授权恢复；四个写入区域再次通过 esptool 哈希校验。

## Reproducible Commands

Normal build:

```bash
source "$HOME/.espressif/v6.0.1/esp-idf/export.sh"
idf.py -C firmware build
```

Parser self-test:

```bash
python3 scripts/firmware/verify_m2_lifecycle.py --self-test
```

Build the stress profile without changing `firmware/sdkconfig`:

```bash
source "$HOME/.espressif/v6.0.1/esp-idf/export.sh"
STRESS_BUILD="$PWD/firmware/build/m2-stress"
idf.py -C firmware \
  -B "$STRESS_BUILD" \
  -D SDKCONFIG="$STRESS_BUILD/sdkconfig" \
  -D 'SDKCONFIG_DEFAULTS=components/gen_bmgr_codes/board_manager.defaults;sdkconfig.defaults;sdkconfig.defaults.m2-stress' \
  build
```

`components/gen_bmgr_codes/board_manager.defaults` is generated by the required board-selection step and supplies the selected board's device symbols. For device verification, flash only after separate authorization, start the serial reader, and then let an operator reset the device. The parser never resets the board and never sends app lifecycle commands:

```bash
python3 scripts/firmware/verify_m2_lifecycle.py \
  --port /dev/cu.usbmodem2101 \
  --output m2-lifecycle.log
```

## Result

`PASS`（2026-09-26）

Source remediation, fresh normal/stress firmware builds, JSON validation, Host verifier self-tests, the separately authorized 50/50 device lifecycle/heap run, and the physical Launcher/Hello/Increment/Home/Launcher path all passed. Earlier images remain superseded; the accepted normal image is currently restored on the device. No commit, tag, push, PR, or release was performed.
