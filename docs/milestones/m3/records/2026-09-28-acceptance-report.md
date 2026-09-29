# M3 验收报告

> 文档类型：历史验收记录。2026-09-29 迁移到 `records/`；原有日期、状态、结果、失败、豁免和证据 identity 保持不变。当前阶段判定见 `../acceptance.md`。

## 状态

- Source/build integration: `PASS`
- Toolkit install/doctor/debug package build: `PASS`
- Boot-time Runtime discovery: `PASS`（clean formal image）
- Interactive Runtime lifecycle and Native coexistence: `PASS`（clean formal image）
- Core `.bpk` install path: `ACCEPTED BY PROJECT OWNER`（无新增原始日志）
- M3: `PASS`（2026-09-28）
- M2: `PASS`（2026-09-26）
- M1: `PASS`（2026-09-25，`v0.1-system`）
- M0: `WAIVED`（2026-09-25，非 PASS）

项目所有者于 2026-09-26 明确授权解析并构建 `espressif/brookesia_runtime_js@0.8.3`（包括 `quickjs-ng@0.14.*`），以及安装/执行 `esp-brookesia-toolkit@1.0.1` 来构建 Hello Runtime `.bpk`。授权后的全新隔离 ESP-IDF 构建成功，以下 firmware、lock、link map、staging 与 LittleFS 证据均来自该运行。更早由只读复核 agent 越界产生的 build、lock 和 managed components 仍保留在会话临时隔离区，继续不作为证据。

项目所有者随后逐项命名授权所有相关外部源码。`esp-brookesia-toolkit@1.0.1` 已安装并生成 JavaScript lock；官方 `doctor` 与 `build` 已运行，产出 debug `.bpk`。2026-09-26 的授权 clean-image 设备验证证明 boot-time staged Runtime 可被 System Core 安装，并完成 Runtime 可见性、渲染、启动/停止、Home 返回及 Native/Runtime 双向交替。2026-09-28，项目所有者确认 M3 可直接判定 `PASS`，不再把独立 Core `.bpk` file-install 作为 M3 阻塞门槛；本次确认没有新增可留存的原始设备日志。

## Scope

- 仅启用官方 JavaScript Runtime，不增加 Lua、WASM、ELF 或私有 Runtime。
- 新增最小 `Hello Runtime` 源包，stable package ID 为 `espocket.app.hello_runtime`。
- Circular Shell Launcher 同时保留固定的 `Hello Native` 与 `Hello Runtime` 入口。
- 使用 System Core 官方 runtime staging helper 和现有 `littlefs_data` 分区。
- 使用官方 `.bpk` 与 Toolkit；不创建 ESPocket 私有包格式或 CLI。

## Static Integration

| 检查项 | 实现/证据 | 状态 |
|---|---|---|
| Runtime dependency declaration | `espressif/brookesia_runtime_js: "0.8.3"` | IMPLEMENTED |
| Runtime auto-registration | `CONFIG_BROOKESIA_RUNTIME_JS_ENABLE_AUTO_REGISTER=y` | IMPLEMENTED AND BUILT |
| Package discovery | `install_registered_apps=false`；`install_package_apps=true` | IMPLEMENTED AND BUILT |
| Storage | HAL StorageFs + LittleFS enabled；只允许 `littlefs_data` mount-failure format | IMPLEMENTED AND BUILT |
| Runtime source package | `manifest.json`、`app/main.js`、`res/` | IMPLEMENTED |
| Product compatibility | manifest declares `systems: ["espocket"]` | IMPLEMENTED |
| GUI | fixed label `Hello from JavaScript` | IMPLEMENTED |
| Launcher | fixed manifest-ID lookup for Native and Runtime entries | IMPLEMENTED |
| Firmware staging | official `runtime_app_stage.cmake` helper stages source to the Core app root | PASS |
| LittleFS image | official `littlefs_create_partition_image(... DEPENDS ...)` wiring | PASS |
| Toolkit project | exact `esp-brookesia-toolkit@1.0.1` dev dependency, npm lock, and official CLI scripts | PASS |
| Static package references | manifest entry, profile root, assets, and screen-flow references | PASS |
| Patch whitespace | `git diff --check` | PASS |

## Build and Dependency Evidence

Accepted build command used ESP-IDF 6.0.1, generated Board Manager defaults, an isolated build directory, and an isolated generated `SDKCONFIG`:

```bash
source "$HOME/.espressif/v6.0.1/esp-idf/export.sh"
idf.py -C firmware \
  -B "$CLAUDE_JOB_DIR/tmp/m3-m5-clean-12k-build" \
  -D SDKCONFIG="$CLAUDE_JOB_DIR/tmp/m3-m5-clean-12k-build/sdkconfig" \
  -D 'SDKCONFIG_DEFAULTS=components/gen_bmgr_codes/board_manager.defaults;sdkconfig.defaults' \
  build
```

| 检查项 | 状态 | 证据 |
|---|---|---|
| ESP-IDF Component Manager resolution | PASS | fresh authorized resolution completed during configure/build |
| `brookesia_runtime_js` exact lock | PASS | version `0.8.3`；component hash `be4ae9c11b34b259ea9148fb3b4f475125587849d2b635bc2c8c5026883359cb` |
| `quickjs-ng` exact lock | PASS | version `0.14.0`；component hash `51ead31abca34af01a44df24128e9ea10331cf35beb976a18fae62a03d36d6e2` |
| Lock manifest identity | PASS | accepted M3 build used `manifest_hash: 9cdc6dc56a1a5776515b23f50332e175dedd93e37058ba4be8bef54131cacff6`; the cumulative lock later advances with authorized M4/M5 dependencies |
| Runtime auto-register config | PASS | generated `sdkconfig.h` defines `CONFIG_BROOKESIA_RUNTIME_JS_ENABLE_AUTO_REGISTER 1` |
| Runtime linker retention | PASS | final `espocket.map` contains `runtime_js_backend_symbol` |
| Firmware build | PASS | final clean `espocket.bin` is `0x5cc1c0` / 6,078,912 bytes；smallest app partition has `0x474e40` bytes free |
| Firmware SHA-256 | PASS | `03642f156ace69ab35dc853bc86c950569e5ce50b206f691baa27cccf05123e1` |
| Staged app tree | PASS | build log stages `/littlefs/apps/espocket.app.hello_runtime` and lists manifest, JS entry, profile, root, flow, and screen files |
| `littlefs_data` image | PASS | final cumulative image: 5,120,000 bytes；SHA-256 `576301fde75b758b679ec178fb3a9a9828bf75f6a6ff1dd24c388acff01b55bb` |
| Toolkit install | PASS | npm installed 62 packages; `esp-brookesia-toolkit` locked to `1.0.1`; audit reports 0 vulnerabilities |
| Toolkit doctor | PASS (HOST) | Node 22.22.2, native BPK packager, and WASM simulator detected; USB CLI/device absent as expected because this run excludes flashing |
| Toolkit debug build | PASS | official `brookesia build` completed in 23 ms |
| JavaScript dependency lock | PASS | npm lockfile v3 records exact Toolkit version, registry URL, and integrity digest |
| `.bpk` structure | PASS | standard ZIP with `manifest.json`, `app/main.js`, and `res/` GUI files; CRC test passed |
| `.bpk` identity | PASS | `espocket.app.hello_runtime.debug.0.1.0.bpk`; SHA-256 `30e406b48008db5931f081a91117b93f8ad4772d91d31f6aff6105971e56ffdf` |
| Packaged manifest | PASS | semantic match to source; Toolkit adds empty `services`; package supports exact system `espocket` |
| Packaged JavaScript | PASS | `app/main.js` byte-identical to source and passes `node --check` |
| Release signature | NOT CREATED | debug build intentionally contains no `META-INF/hash.json` or `META-INF/signature.sig`; official verifier rejects it as unsigned; no private-key operation authorized |

`brookesia_stage_runtime_app_package()` copies the unpacked source tree into the boot image. Device logs prove that System Core discovers and installs this staged package as `manifest(espocket.app.hello_runtime)`. This does **not** independently prove the Core `.bpk` verification, update, or uninstall paths; the project owner accepted that evidence boundary when marking M3 `PASS`.

## Runtime Lifecycle and Hardware

| 检查项 | 状态 | 备注 |
|---|---|---|
| Boot discovers Hello Runtime | PASS (CLEAN) | System Core installed App ID 5 with `manifest(espocket.app.hello_runtime)` before `ESPocket started` |
| Launcher shows Native + Runtime | PASS (PHYSICAL) | project owner confirmed both entries visible on the clean image |
| Start Runtime App | PASS (PHYSICAL + SERIAL) | two Runtime starts recorded by Runtime Manager/System Core |
| Render `Hello from JavaScript` | PASS (PHYSICAL) | project owner confirmed expected text |
| Home stops Runtime App | PASS (PHYSICAL + SERIAL) | two Runtime stops recorded after Home |
| Launcher restores | PASS (PHYSICAL) | restored after Native, Runtime, Settings, and Store |
| Native/Runtime alternation | PASS (PHYSICAL + SERIAL) | start sequence contains `Runtime → Native → Runtime`; each start has a matching stop |
| Runtime cleanup/stability | PASS (SMOKE) | Native 3/3 and Runtime 2/2 start/stop pairs; no fatal/reboot signal during combined window |
| Official `.bpk` install path | ACCEPTED (OWNER CONFIRMATION) | no new raw log retained; unpacked staging alone is not file-install evidence |

The accepted cumulative image and isolated diagnostic canaries were flashed under explicit authorization without whole-chip/NVS erase. The first accepted image repeatedly overflowed the 64 KiB System workers. A 128 KiB canary removed that failure but exposed the missing official JPEG decoder gate. After enabling `CONFIG_ESP_LVGL_ADAPTER_ENABLE_DECODER=y`, a repeated no-input 60-second boot completed with one ROM banner, no fatal signal, and all four product apps installed. A later 16 KiB Service Manager secondary-worker canary failed deterministically before GUI startup because its two internal-SRAM stacks left no contiguous 46,600-byte LVGL secondary display buffer; the same failure reproduced after reset. This is diagnostic evidence, not a Runtime lifecycle result.

## Device Boot Recovery Observations

| Scenario | Observation |
|---|---|
| 64 KiB Core workers | 7 ROM banners, 6 reboots, 6 `System0/System2` stack overflows, 0 `ESPocket started` |
| 128 KiB Core workers before JPEG gate | Original overflow removed; Settings then failed because the official adapter decoder gate was disabled |
| JPEG-enabled Store canary | Reached `ESPocket started`; a later Store run overflowed the separate `SvcMgrSec0` worker and rebooted |
| Repeated no-input 60-second boot | One ROM banner, all product apps installed, one `ESPocket started`, no app open, reboot, overflow, panic, WDT, assert, heap corruption, or startup failure |
| 16 KiB × 2 secondary stacks | Deterministic 46,600-byte LVGL secondary-buffer allocation failure before app installation/startup |
| 16 KiB reset retry | Same allocation failure reproduced at the same startup stage; no panic, overflow, or reboot loop |
| 12 KiB unattended 180-second boot | All product apps installed, no touch/Store-open event or fatal signal, `SvcMgrSec0/1` minimum-free 7,300 / 7,296 bytes |
| 12 KiB directed 240-second Store window | One physical `pressed → Store open → released` sequence, no fatal/reboot signal, final `SvcMgrSec0/1` minimum-free 7,300 / 3,600 bytes |
| Clean 90-second formal-image boot | All five apps installed, one `ESPocket started`, no Store autostart or fatal/reboot signal |
| Clean combined physical pass | Native 3/3, Runtime 2/2, Settings 1/1, Store 1/1 start/stop pairs; `Runtime → Native → Runtime`; no fatal/reboot signal |

The stable 128 KiB canary reported minimum-free values of 55,648 / 126,600 / 88,632 bytes for `System0/1/2`. The maximum observed use was therefore 75,424 bytes. Applying the fixed policy

```text
target = ceil((maximum_used + 16384) / 4096) * 4096
```

selects `CONFIG_BROOKESIA_SYSTEM_CORE_WORKER_STACK_SIZE=94208`, leaving 18,784 bytes of observed reserve. This value applies only to System Core workers. The separate Service Manager workers were measured independently: ESP-IDF and Brookesia both express their configured stack and high-water mark in bytes, and the Store path used at most 8,688 of 12,288 bytes. The tracked formal value is therefore `CONFIG_BROOKESIA_SERVICE_MANAGER_SECONDARY_SCHEDULER_WORKER_STACK_SIZE=12288`, retaining 3,600 bytes of observed reserve while preserving enough internal SRAM for the existing LVGL buffers.

## Follow-up Boundaries

1. Re-test Core `.bpk` install if a later release needs auditable file-install evidence; boot-time unpacked staging and Host-side Toolkit output are not substitutes.
2. Decide and authorize a release-signing procedure before generating private keys or claiming a verified release package. Signing remains a release/M5 concern, not an M3 blocker.
3. No further interactive Runtime lifecycle work is required for M3; repeat only after a platform/runtime upgrade.

## Result

`PASS`（2026-09-28）

The Runtime JS/QuickJS dependency resolution, clean firmware build/boot, staged package tree, LittleFS image, Toolkit debug `.bpk`, physical Runtime lifecycle, Home restoration, and Native coexistence are accepted. On 2026-09-28 the project owner accepted M3 as `PASS` without retaining an additional Core `.bpk` file-install log. The debug package remains intentionally unsigned; release verification is tracked separately and is not implied by this result.
