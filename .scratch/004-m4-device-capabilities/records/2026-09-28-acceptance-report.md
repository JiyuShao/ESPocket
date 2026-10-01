# M4 验收报告

> 文档类型：历史验收记录。2026-09-29 迁移到 `records/`；原有日期、状态、结果、失败、豁免和证据 identity 保持不变。当前工作与结果见 [对应 Spec](../spec.md)；本页只保存历史事实。

## 状态

- Source integration: `PASS`
- Dependency resolution: `PASS`
- Firmware build/link/staging: `PASS`
- Settings boot-time install: `PASS`（clean formal image）
- Settings lifecycle and 466×466 UI smoke: `PASS`（physical）
- Wi-Fi page / Brightness / Time / Battery / Device info: `PASS`（physical；Time/Battery owner-confirmed）
- System keyboard provider: `PASS (HOST BUILD + PHYSICAL SEMANTICS)`（owner-confirmed）
- Wi-Fi initialize / preserved-NVS reconnect / SNTP: `PASS (DEVICE)`
- Storage / Developer controls: `NOT TESTED`
- Sound/Volume capability: `BLOCKED`
- M4: `BLOCKED`
- M3: `PASS`（2026-09-28）
- M2: `PASS`（2026-09-26）
- M1: `PASS`（2026-09-25，`v0.1-system`）
- M0: `WAIVED`（2026-09-25，非 PASS）

M4 复用官方 `brookesia_app_settings@0.8.3` 与 `brookesia_service_audio@0.8.2`，不复制官方资源、不修改 `managed_components/`、不增加 ESPocket 私有 Settings 或 Audio framework。项目已解析并锁定两个官方组件，项目所有者也已逐项命名授权相关外部源码。修正 build-local Board Manager defaults、worker stack 与严格 Audio-disabled 边界后，全新 ESP32-S3 clean build、稳定启动和 Settings 物理 smoke 均通过。2026-09-27 键盘/Wi-Fi 候选随后完成 app-only 写入和 90 秒真机启动验证；Wi-Fi 以实际 10 个静态 RX buffer 初始化，保留 NVS 下网络就绪且 SNTP 同步完成。脱敏串口确认键盘 provider 在同一 boot 中完成一次 matching open/close；2026-09-28，项目所有者进一步确认键盘屏上语义、Time 与 Battery 均无问题。M4 仍因 Storage/Developer 未单独确认以及 Sound/Volume 上游能力边界而 `BLOCKED`。

## Source Integration

| 检查项 | 实现/证据 | 状态 |
|---|---|---|
| Settings component | `espressif/brookesia_app_settings: "0.8.3"` | PASS |
| Audio component | `espressif/brookesia_service_audio: "0.8.2"` | PASS |
| Product composition | `espocket::System::on_init()` 显式构造并 `install_app(SettingsApp)` | PASS |
| Provider behavior | 保持 `install_registered_apps=false`；不启用全局隐式 App provider 安装 | PASS |
| Launcher | fixed `brookesia.general.settings` manifest ID、`shell.open_settings` action；复用现有 `open_app()` | PASS |
| Circular layout guard | 品牌、caption 与三个 48dp 按钮的 fixed content height 为 230dp | PASS (STATIC) |
| Settings resources | official staging target → 46 files / 236,537 bytes；与组件 source 逐字一致；全部 36 个 JSON 可解析 | PASS |
| System keyboard provider | `espocket::System` 实现 Core keyboard hooks；Circular Shell 提供 transient native-LVGL overlay | PASS (HOST BUILD + PHYSICAL; OWNER CONFIRMED) |
| Keyboard contract | password immediate-mask；`max_length` 先于 `initial_text`；受限 `allowed_modes` fail-closed | PASS (STATIC + BUILD) |
| Private framework/managed patch | 无私有输入 framework；未修改 `managed_components/` | PASS |
| Embedded JSON/action wiring | 标准 JSON parser + 三个 fixed action/manifest 静态检查 | PASS |
| Patch whitespace | `git diff --check` | PASS |

## Dependency Resolution

首次隔离 configure 使用 ESP-IDF 6.0.1、Board Manager defaults 与独立 generated `SDKCONFIG`。Component Manager 成功解析 41 项依赖并更新 `firmware/dependencies.lock`。

| Component | Version | Component hash | 状态 |
|---|---:|---|---|
| `espressif/brookesia_app_settings` | 0.8.3 | `46dd5de734a74672203240420fd52967b3f61f9882b600813d24b1fccd3204a5` | PASS |
| `espressif/brookesia_service_audio` | 0.8.2 | `fa2c42fa777aad7b2f5b8dab3829c7e2448fd211f3dc29418eb1353662e53afc` | PASS |

The M4-only resolution produced manifest hash `738b17ba408c1e4857f82a50a93671c074806198ad7de620173cfe9bca6eadac`. The current cumulative M3–M5 lock later advanced to `9837e1c6294dd3a90103ea18aa2e89a0d1c91815b5557dadcb90d412c08a8104` when authorized Store/HTTP dependencies were added; the Settings and Audio versions/hashes above did not change.

The accepted source configuration now expresses the build-safe strict boundary:

```text
# CONFIG_BROOKESIA_HAL_ADAPTOR_ENABLE_AUDIO_DEVICE is not set
# CONFIG_BROOKESIA_SERVICE_AUDIO_ENABLE_AUTO_REGISTER is not set
CONFIG_BROOKESIA_APP_SETTINGS_ENABLE_PRELOAD_DOM=y
```

HAL Adaptor child implementation symbols are intentionally not assigned while their parent is disabled; invisible Kconfig symbols are omitted rather than exported as false.

## Prior Clean Firmware Baseline

The prior clean baseline uses ESP-IDF 6.0.1, target `esp32s3`, a build-local `sdkconfig`, and defaults in this order:

```text
components/gen_bmgr_codes/board_manager.defaults
sdkconfig.defaults
```

| Evidence | Result |
|---|---|
| Ninja build | `1959/1959`, exit code 0 |
| Failure scan | no `error`, `FAILED`, traceback, undefined reference, or stopped Ninja record |
| Settings source compile | official Settings C++ translation units compiled |
| Settings linker retention | final ELF contains `SettingsApp::get_manifest()` |
| Firmware image | 6,078,912 bytes (`0x5cc1c0`) |
| Firmware SHA-256 | `03642f156ace69ab35dc853bc86c950569e5ce50b206f691baa27cccf05123e1` |
| Factory partition headroom | 4,673,088 bytes (`0x474e40`, 43%) |
| LittleFS image | 5,120,000 bytes |
| LittleFS SHA-256 | `576301fde75b758b679ec178fb3a9a9828bf75f6a6ff1dd24c388acff01b55bb` |
| Settings staged tree | 46 files / 236,537 bytes; byte-identical to official package source |
| Image inclusion | LittleFS creation log explicitly adds `apps/brookesia.general.settings` and its files |

An earlier image was flashed under explicit authorization and preserved NVS, but it repeatedly overflowed the default 64 KiB System Core workers during Settings DOM preload. Diagnostic canaries identified the required JPEG decoder gate and measured worker stacks. The resulting clean baseline app image (`03642f156ace69ab35dc853bc86c950569e5ce50b206f691baa27cccf05123e1`) was then flashed app-only, passed a 90-second fail-closed boot, and completed a physical Settings open/browse/device-page/Home smoke with no reported UI anomaly or fatal signal. It was the accepted baseline before the 2026-09-27 keyboard/Wi-Fi candidate below; the current hardware image is the later M5 HTTP-containment build, which retains the same M4 keyboard and Wi-Fi changes.

The recovery sequence, clean boot, combined physical lifecycle counts, and worker calculations are retained in [M3 acceptance](../../003-m3-runtime-app/spec.md).

## 2026-09-27 Keyboard/Wi-Fi Candidate and Current Containment Image

The subsequent Wi-Fi attempt exposed two independent blockers in the accepted image: ESPocket did not provide System Core's keyboard hooks, and ESP-IDF could allocate only 11 of the configured 16 static Wi-Fi RX buffers before returning `ESP_ERR_NO_MEM`. The Settings Wi-Fi page was reached without a successful enable/connect result. The keyboard investigation and static-RX allocation failure contained no password or connection target.

The product-only candidate now forwards the official keyboard request/completion hooks to a transient Circular Shell LVGL overlay and changes Wi-Fi RX/BA values to 10/10. It preserves the accepted 50-row double display buffers, 94,208-byte Core workers, and 12,288-byte secondary workers. Full build/link and image validation pass, and the final ELF has zero delta in `.dram0.data`, `.dram0.bss`, `.iram0.text`, and `.iram0.vectors` versus the accepted clean ELF.

Static review also found that Core 0.8.4 broadcasts `KeyboardClosed.Text` service-wide. Normal Runtime stop releases subscriptions, but a hostile Runtime can fail its lifecycle `on_stop` before cleanup and leave a listener resident. ESPocket cannot owner-filter this managed event without an upstream API, so the candidate accepts keyboard requests only from a `Running` owner app, then latches any Runtime stop failure and makes all later keyboard requests fail closed until restart. Normal successful Runtime operation remains enabled; owner-scoped delivery and unconditional failed-stop cleanup remain upstream requirements.

| Candidate evidence | Result |
|---|---|
| Firmware image | 6,087,072 bytes (`0x5ce1a0`) |
| Firmware SHA-256 | `594708e9f62d42fc58cf0648913f795b65aac35c2d9fba589ad3cde352d39e37` |
| ELF SHA-256 | `e0515a7fce1c33658eea00238fab2374f18a82f3ec925d4d2c7279f826f22370` |
| App-partition headroom | `0x472e60` bytes (43%) |
| LittleFS SHA-256 | `576301fde75b758b679ec178fb3a9a9828bf75f6a6ff1dd24c388acff01b55bb` (byte-identical to accepted image) |
| Image header/checksum/hash | ESP32-S3, DIO, 80 MHz, 16 MB; valid checksum and validation hash |
| Device write | PASS — app-only write at `0x60000`; esptool written-data hash verified; bootloader/partition table/NVS/LittleFS excluded |
| 90-second boot validator | PASS — exactly one ROM banner; `required_missing=[]`; `fatal_signals=[]` |
| Wi-Fi initialization | PASS (DEVICE) — actual static RX buffer count 10; no shortfall, `ESP_ERR_NO_MEM`, or initialization failure |
| Network / SNTP | PASS (DEVICE) — credential-safe capture observed network ready and completed SNTP synchronization |
| Physical keyboard provider lifecycle | PASS — matching open/close retained in serial evidence; visual/semantic behavior confirmed by project owner on 2026-09-28 |

The host-build phase completed before any device write. The later device run verified the app-only write, a 90-second boot, 10 static RX buffers, network readiness, and SNTP synchronization. A subsequent interaction recorded exactly one matching keyboard open/close. The current hardware image is the later M5 HTTP-containment app (`870c7031dfa64dd20347d0879e3753608df37365973a07b609c2697ca98cf72b`), which retains this keyboard implementation and Wi-Fi 10/10 policy. No keyboard interaction was performed during that later retained capture; the project owner separately confirmed the keyboard's masking, modes, typed-input, confirm/cancel, and visual-cleanup semantics on 2026-09-28, without retaining credential-bearing material.

## Audio Capability Boundary

M4 does not silently enable recording merely to make the official Sound page available.

Source and configure analysis proves:

1. Official `AudioPlayback::on_start()` unconditionally acquires `hal::audio::PlaybackIface`.
2. HAL Adaptor publishes `PlaybackIface` only through Audio Processor; the independently selectable Codec Player exposes a lower-level `CodecPlayerIface` instead.
3. Audio Processor Kconfig depends on both Codec Player and Codec Recorder.
4. With `recorder=n`, the processor symbol becomes invisible rather than a readable false value, so no `PlaybackIface` is registered.
5. HAL Adaptor 0.8.4 nevertheless references that processor symbol in Component Manager dependency conditions, causing `Missing required kconfig option after retry` in the attempted official Audio-service configuration.
6. Enabling recorder would make the official service path resolvable but violate ESPocket's playback-only product boundary; patching or copying `managed_components/` is also forbidden.

Result:

| Capability | 状态 | 备注 |
|---|---|---|
| Audio Device HAL | DISABLED | product does not enable a partial HAL that cannot satisfy the official Audio-service contract |
| Codec player HAL | DISABLED (PRODUCT) | can be selected without recorder, but exposes `CodecPlayerIface`, not the `PlaybackIface` required by `AudioPlayback` |
| Codec recorder HAL | DISABLED | product constraint |
| Audio processor | DISABLED | requires both player and recorder |
| AudioPlayback service | DISABLED | prevents ServiceManager startup failure without `PlaybackIface` |
| Settings Sound/Volume | BLOCKED | unavailable until the official HAL/Audio-service path provides playback control with recorder disabled |

This is a verified upstream HAL/Audio-service capability boundary, not a reason to fork HAL, patch managed code, enable the unwanted HAL Adaptor recorder implementation, or claim a false PASS. The 2026-09-28 released-version and immutable-`master` recheck is recorded in [`../upstream/status-2026-09-28.md`](../../../docs/upstream/status-2026-09-28.md); it found no official playback-only fix.

## Settings Resource and Round-Screen Boundary

Official Settings 0.8.3 variants include exact 1024×600, 800×480, 480×480, portrait, and default profiles. ESPocket exposes 466×466 at density 1.0, so it falls back to the default profile; no official `466`, `round`, or circular-safe profile exists.

| Check | 状态 |
|---|---|
| Official resource staging | PASS |
| LittleFS image contains `brookesia.general.settings` | PASS (BUILD LOG) |
| System Core installs Settings on device | PASS (CLEAN) |
| Launcher Settings button visible/safe | PASS (PHYSICAL) |
| Settings opens/stops/Home restores Launcher | PASS (PHYSICAL + SERIAL) |
| 466×466 clipping/touch/scroll | PASS (PHYSICAL SMOKE; no anomaly reported) |

## Device Capability Matrix

| M4 capability | Source path | 状态 |
|---|---|---|
| Wi-Fi page reachability | Official Settings + existing Wi-Fi/Storage services | PASS (PHYSICAL UI SMOKE) |
| Password keyboard | System Core hook + Circular Shell LVGL overlay | PASS (PHYSICAL; OWNER CONFIRMED); no credential-bearing evidence retained |
| Wi-Fi initialize/connect | Official Settings + Wi-Fi service; RX/BA 10/10 | PASS (DEVICE; actual RX 10, network ready, no memory/init failure) |
| SNTP synchronization | Official SNTP service after network connection | PASS (DEVICE; synchronization completed) |
| Brightness | Official Settings + existing Display/Backlight service | PASS (PHYSICAL ADJUSTMENT) |
| Volume/mute | Official Settings + AudioPlayback | BLOCKED (Audio Device disabled; upstream playback-only config is not resolvable) |
| Time/timezone | Official Settings + existing SNTP/Storage services | PASS (PHYSICAL; OWNER CONFIRMED) |
| Storage visibility | Official Settings device data | NOT TESTED |
| Battery | Official Settings/Device data; not a full battery management page | PASS (PHYSICAL; OWNER CONFIRMED) |
| Device info | Official Settings + Device service | PASS (PHYSICAL SMOKE) |
| Developer/debug controls | Official Settings debug UI | NOT TESTED |
| Files | intentionally not added | OUT OF SCOPE |

## Required Unblock

1. Exercise Storage visibility and Developer/debug controls on hardware.
2. Consume an official HAL/Audio-service fix that provides the `PlaybackIface` required by `AudioPlayback` with Codec Player enabled and Codec Recorder disabled before Sound/Volume can pass without violating the product constraint.

## Result

`BLOCKED`

The official Settings integration, exact dependency resolution, 466×466 interaction smoke, Wi-Fi page, Brightness, Time, Battery, Device UI, keyboard semantics, and Home restoration are accepted. The current app-only image also passed a one-banner 90-second boot, initialized Wi-Fi with all 10 configured static RX buffers, reached the preserved-NVS network, and completed SNTP synchronization without a fatal signal. M4 remains `BLOCKED` only for the outstanding Storage/Developer checks and the Sound/Volume upstream playback-only boundary.
