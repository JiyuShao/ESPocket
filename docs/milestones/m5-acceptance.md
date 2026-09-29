# M5 验收报告

## 状态

- Source integration: `PASS`
- Static trust analysis: `PASS`
- Dependency resolution: `PASS`
- Firmware build/link/staging: `PASS`
- Device Store startup/Home return: `PASS (CLEAN FORMAL IMAGE, OFFLINE)`
- Remote index transfer: `PASS (PRIOR 2/2 + CURRENT 1/1, DEVICE)`
- Initial metadata HTTPS transfer: `PASS (PRIOR 2/2 IMAGE, DEVICE)`
- Prior 2-worker/2-concurrent online Store stability: `FAIL (DEVICE PANIC / REBOOT)`
- 1-worker/1-concurrent containment write and clean boot: `PASS (DEVICE)`
- 1-worker/1-concurrent cached Store lifecycle/Home return: `PASS (DEVICE)`
- 1-worker/1-concurrent remote index/cache transfer: `PASS (DEVICE)`
- 1-worker/1-concurrent online Store stability: `FAIL (LOADPROHIBITED / REBOOT)`
- Package trust/catalog compatibility: `BLOCKED`
- Runtime keyboard-event isolation: `BLOCKED (UPSTREAM)` / `CONTAINED (PRODUCT FAIL-CLOSED)`
- M5: `BLOCKED`
- M4: `BLOCKED`
- M3: `PASS`（2026-09-28）
- M2: `PASS`（2026-09-26）
- M1: `PASS`（2026-09-25，`v0.1-system`）
- M0: `WAIVED`（2026-09-25，非 PASS）

M5 使用官方 `brookesia_app_store@0.8.2`、System Core package lifecycle、official HTTP/Storage services 与 Runtime JS。没有创建 ESPocket 私有 Store backend、downloader、package manager、package format 或 provider；没有 vendor 或修改 `managed_components/`。

项目所有者已逐项命名授权 `espressif/brookesia_app_store@0.8.2` 及其 Registry 依赖。Component Manager 已将 Store 0.8.2 与 HTTP 0.8.2 精确解析到当前 lock；修正 build-local Board Manager defaults 与严格 Audio-disabled 边界后，全新 ESP32-S3 隔离构建完成。Store、HTTP、TLS policy、资源 staging、LittleFS image 与 clean-image 离线 Store lifecycle 均有证据。2026-09-27 先前的 2-worker/2-concurrent 在线真机流程成功下载并缓存远程索引及部分元数据，但并发请求/取消期间出现 TLS setup failures，随后发生一次 `LoadProhibited`、两次 `StoreProhibited` 与三次自动重启。后续 1-worker/1-concurrent containment 镜像已 app-only 写入并通过 written-data hash、单 ROM banner 90 秒启动、Wi-Fi RX 10 与 SNTP 验证。第一次脱敏窗口没有实际打开 Store；第二次物理交互记录了一次 Store start/open、缓存索引与 5 个 metadata 加载，以及匹配的 HTTP/App stop，Home 清理无 fatal signal。HTTP 因 SNTP 延迟才进入 Started，此后至 Home 前没有提交远程请求，所以该次只证明缓存态生命周期。最后的显式 Refresh 真机验证成功提交远程索引与图标请求并多次写入 index cache，且未再出现 `-0x008D`；但一次 index 连接超时、HTTP 宣布重试、Store refresh timeout 后立即发生 `LoadProhibited`（`EXCVADDR=0x8`）并自动重启。符号化崩溃任务栈位于 `mbedtls_ssl_handshake_step()` 经 `esp_http_client_open()` 与 Brookesia HTTP worker 的调用链。M5 因当前 1/1 在线稳定性仍失败、package trust、Runtime keyboard-event owner isolation、catalog compatibility、Launcher sync 与完整分发流程而继续 `BLOCKED`。

## Source Integration

| 检查项 | 实现/证据 | 状态 |
|---|---|---|
| Store dependency | `espressif/brookesia_app_store: "0.8.2"` | PASS (RESOLVED) |
| Product composition | `espocket::System::on_init()` 显式构造并 `install_app(AppStoreApp)` | PASS |
| Provider behavior | 保持 `install_registered_apps=false`；不隐式安装所有 provider | PASS |
| Launcher | fixed `brookesia.general.app_store` ID + `shell.open_app_store`；复用 `open_app()` | PASS |
| Launcher layout | Settings / Store 共用 210×48dp row；总 fixed content height 230dp | PASS (STATIC) |
| Official staging wiring | Store official package → 17 files / 72,926 bytes；与组件 source 逐字一致；全部 12 个 JSON 可解析 | PASS |
| Private backend/package/CLI | none | PASS |
| Patch managed source | none | PASS |
| Embedded JSON/action wiring | 4 fixed actions 与 manifest IDs 通过静态检查 | PASS |
| Patch whitespace | `git diff --check` | PASS |

## Dependency Resolution

The authorized ESP-IDF Component Manager run converged to 43 dependencies in the cumulative M3–M5 lock. The final pass includes Board Manager's `espressif/esp_codec_dev@1.5.11` after the selected board defaults were loaded correctly:

| Component | Version | Component hash | 状态 |
|---|---:|---|---|
| `espressif/brookesia_app_store` | 0.8.2 | `ad0bbb0e101e79c88cf1686fe7dc27c3428e8499451ae46b5cac744845eb5036` | PASS |
| `espressif/brookesia_service_http` | 0.8.2 | `501a2ccff2c76005696f513e207de6cea1abd4d2eed630c5c6ac19f5ae11cb6f` | PASS |
| `espressif/esp_codec_dev` | 1.5.11 | `df70f10af8d7b922add7b9d07372c9c97ab356e58d72b7a892050227c2d44348` | PASS (Board Manager hardware dependency; Audio service remains disabled) |

Current cumulative lock manifest hash: `9837e1c6294dd3a90103ea18aa2e89a0d1c91815b5557dadcb90d412c08a8104`.

The successful final build preserves these exact resolved versions and hashes.

## Offline Store Baseline Build

The accepted offline-Store baseline uses ESP-IDF 6.0.1, target `esp32s3`, a build-local `sdkconfig`, and defaults in this order:

```text
components/gen_bmgr_codes/board_manager.defaults
sdkconfig.defaults
```

| Evidence | Result |
|---|---|
| Ninja build | `1959/1959`, exit code 0 |
| Failure scan | no `error`, `FAILED`, traceback, undefined reference, or stopped Ninja record |
| Store / HTTP compile | official Store sources compiled; HTTP static library linked |
| Final ELF symbols | `AppStoreApp::get_manifest()` and `SettingsApp::get_manifest()` present; Runtime JS backend retained; 487 HTTP namespace symbols observed |
| Final map | Store, HTTP, Settings, and Runtime JS archives retained |
| Firmware image | 6,078,912 bytes (`0x5cc1c0`) |
| Firmware SHA-256 | `03642f156ace69ab35dc853bc86c950569e5ce50b206f691baa27cccf05123e1` |
| Factory partition headroom | 4,673,088 bytes (`0x474e40`, 43%) |
| LittleFS image | 5,120,000 bytes |
| LittleFS SHA-256 | `576301fde75b758b679ec178fb3a9a9828bf75f6a6ff1dd24c388acff01b55bb` |
| Store staged tree | 17 files / 72,926 bytes; byte-identical to official package source |
| Image inclusion | LittleFS creation log explicitly adds `apps/brookesia.general.app_store` and its files |

The earlier accepted image failed before full startup because the default 64 KiB System Core worker stack overflowed during Settings DOM preload. Diagnostic canaries then identified the JPEG decoder gate, measured the formal 94,208-byte System workers and 12 KiB secondary workers, and rejected 16 KiB secondary workers because they exhausted the internal-SRAM display-buffer budget. The final clean image above was flashed app-only under explicit authorization, passed a 90-second fail-closed boot, and completed Store start, Offline network handling, Home stop, and Launcher restoration without a fatal signal.

The later 2026-09-27 app-only candidate (`594708e9f62d42fc58cf0648913f795b65aac35c2d9fba589ad3cde352d39e37`) was written only at `0x60000` and passed a one-ROM-banner 90-second validator run. Wi-Fi allocated all 10 configured static RX buffers without memory or initialization failure, and a credential-safe capture observed network readiness followed by completed SNTP synchronization. That first capture did not open Store; its retained summary is `evidence/m4/M4_KEYBOARD_WIFI_DEVICE_BOOT_2026-09-27.txt` (SHA-256 `cec46292215317dbb07d7249eb4765983b67a0a5a56daf72530049f7fa550810`).

A later credential-safe online Store interaction submitted the official HTTPS index request, wrote the remote index cache, and wrote several metadata cache files, proving successful remote-index and initial HTTPS transfer. The same capture then recorded 14 `mbedtls_ssl_setup` failures (`-0x008D`), one `LoadProhibited`, two `StoreProhibited` panics, and three automatic reboots across consecutive Store runs. The fourth boot recovered without opening Store. The sanitized evidence is `evidence/m5/M5_ONLINE_STORE_CRASH_2026-09-27.txt` (SHA-256 `e0d9ed7173cc3969bad7bb624c106acacf607412a5e03fe701906a3fe800be47`); it contains no SSID or password value.

Locked-source analysis confirms `-0x008D` is Mbed TLS 4.0.0's `MBEDTLS_ERR_SSL_ALLOC_FAILED`, mapped to PSA status `-141` (`PSA_ERROR_INSUFFICIENT_MEMORY`). The generated firmware uses the internal-only Mbed TLS allocator with 16,384-byte input and 4,096-byte output content lengths, so concurrent TLS setup exhausts or fragments internal 8-bit RAM rather than PSRAM. Separately, Store invokes scheduler-free `CancelRequest` on its caller thread. HTTP cancellation copies a shared transaction under its mutex, releases that mutex, then calls `cancel()`; the HAL implements this as `esp_http_client_close()` while a worker may still execute `open()`, `read()`, or `is_complete()` without the same operation mutex. ESP-IDF explicitly forbids simultaneous operation of one HTTP client handle from two places, so this is a confirmed unsupported concurrency path. Cancellation immediately precedes every captured panic window, making it the strongest supported panic cause, but the missing PC/EXCVADDR/backtrace prevents claiming the exact faulting instruction. Timer warning 364 is explained by Core clearing App timers before Store's native `on_stop()` and is not treated as UAF evidence.

ESPocket now applies a minimum product containment using only official Kconfig: one HTTP worker and one maximum concurrent request. This prevents overlapping active TLS setup peaks without modifying `managed_components/`, weakening TLS, or adding a private Store layer. It cannot serialize scheduler-free cancel with the active worker transaction, so the upstream close-vs-use defect remains. A fresh full build passed with zero static DRAM/IRAM growth; its image SHA-256 is `870c7031dfa64dd20347d0879e3753608df37365973a07b609c2697ca98cf72b`. The immutable host-build-phase record is `evidence/m5/M5_HTTP_SERIAL_CONTAINMENT_HOST_BUILD_2026-09-27.txt` (SHA-256 `f2eaae013f00c3de54a7de30790efa9dbce357b4e8b8dd234e68977804c9303a`); its statement that no device was written is accurate for that earlier phase.

The same image was subsequently written only at `0x60000` under explicit authorization. Esptool verified the written-data hash, and a credential-safe 90-second validation captured exactly one ROM banner, all required app/system markers, Wi-Fi static RX count 10, network readiness, completed SNTP synchronization, and no fatal signal. A later 600-second observation contained no Store-open or HTTP-request marker; its lack of TLS failure or panic is therefore idle evidence, not online containment validation. The device write/boot record is `evidence/m5/M5_HTTP_SERIAL_CONTAINMENT_DEVICE_BOOT_2026-09-27.txt` (SHA-256 `411d91a13a4f154965ec5b0344a38fb4605ecab6b149946ba78e097961930427`).

A subsequent directed interaction captured one Store start/open, one cached-index load, five cached-metadata loads, HTTP reaching Started after delayed SNTP, and matching HTTP/App stops after the project owner used Home. There was no TLS allocation failure, panic, reboot, or second ROM banner. No HTTP request was submitted, however, so this is a cached-lifecycle/Home-cleanup pass rather than online transport acceptance. The retained summary is `evidence/m5/M5_HTTP_SERIAL_CONTAINMENT_CACHED_LIFECYCLE_2026-09-27.txt` (SHA-256 `230d2ee37f5bc33b45181b1f5893cbdb51f081487240ced80b996378b9849d7a`).

The final directed run used the Store tab's header Refresh action after HTTP was Started. It submitted remote-index and icon requests and wrote the index cache three times across the capture. No `-0x008D` allocation failure occurred. One index request then timed out opening its TLS connection; HTTP announced an immediate retry, Store's source-defined 31-second watchdog fired 31,017 ms after submission, and Core 0 immediately raised `LoadProhibited` with `EXCVADDR=0x8`, followed by automatic reboot. The panic ELF prefix matches the containment ELF. Its symbolized crashing-task stack begins at `mbedtls_ssl_handshake_step()` and proceeds through ESP-TLS, `esp_http_client_open()`, `EspHttpTransaction::open()`, and the sole Brookesia HTTP worker during the second attempt.

Locked source confirms the watchdog dispatches Store timeout handling in SystemApp context and synchronously invokes scheduler-free `CancelRequest`. That path can call destructive `esp_http_client_close()` without an operation mutex while the separate HTTP worker remains blocked in `open()`; ESP-IDF explicitly forbids simultaneous same-handle open/close use. Thus close-versus-handshake TLS-state invalidation is the strongest and most likely cause, and 1/1 demonstrably leaves the unsafe window open. The trace does not include the canceling worker's stack inside `esp_http_client_close()`, so the precise overlap and exact invalid Mbed TLS member remain strongly supported rather than instruction-for-instruction proven.

Retained evidence:

- `evidence/m5/M5_HTTP_SERIAL_CONTAINMENT_ONLINE_FAILURE_2026-09-27.txt` — sanitized serial capture, SHA-256 `83060cddcfaa729895d38f845cb7908585c22c39c3638ed13fe8b74be80f02e5`.
- `evidence/m5/M5_HTTP_SERIAL_CONTAINMENT_ONLINE_FAILURE_SYMBOLIZED_2026-09-27.txt` — address resolution against ELF SHA-256 `cc40c08b4da608962624f7dd4daa4e455a8a3e5efaefa149495a4fe7c8f770e1`, file SHA-256 `c000c9cb914f2e450b273e42935a214a60c61701087a3c9979f97badfb90608f`.
- `evidence/m5/M5_HTTP_SERIAL_CONTAINMENT_ONLINE_FAILURE_SUMMARY_2026-09-27.txt` — conservative event/count and source-timing summary, SHA-256 `e1c5c5399d11681fda2c53f4c00bf8ca55e8a9474b8971ad7a199abc8826f24f`.

Raw Store failure evidence is preserved in:

- `evidence/m3-m5/M3_M5_CANARY_STORE_WORKER_OVERFLOW_2026-09-26.txt` (SHA-256 `0ef2be3a713703230c0e34935718bf0644508e94f9880bc3f4bd93322f89eebe`): Store opened around 13.1 seconds, then `SvcMgrSec0` overflowed.
- `evidence/m3-m5/M3_M5_CANARY_IDLE_STORE_OVERFLOW_2026-09-26.txt` (SHA-256 `08b4b95801cfa5bf1810c0a8fcc1e2d2bfd79d660e8791daedeff5bda6e50caf`): during a 180-second no-input observation, Store opened around 85.9 seconds, then `SvcMgrSec1` overflowed.

The worker rotation proves this is not isolated corruption of one task. Both files are failure evidence, not Store acceptance; the delayed uncommanded Store action is also under investigation. A subsequent 16 KiB-per-worker diagnostic image could not reach GUI startup: on two consecutive boots, the larger pair of internal-SRAM stacks left no contiguous 46,600-byte LVGL secondary display buffer. Those captures are preserved as `evidence/m3-m5/M3_M5_CANARY_16K_SECONDARY_INTERNAL_RAM_FAILURE_2026-09-26.txt` (SHA-256 `5b60f46ac629856b3357726556468c9c9bba48dfe731d0db573fc98afe3d2fc4`) and its reset retry (SHA-256 `10acc1ac439f6ac08e4548a164c6280aefe02c8689d29ecf24a9e3c496cdac23`). Therefore 16 KiB is not a viable product setting under the current display memory policy.

The only 4 KiB-aligned intermediate value, 12 KiB, passed both diagnostic windows:

- 180-second unattended boot: `SvcMgrSec0/1` minimum-free values 7,300 / 7,296 bytes, with no Store-open, touch, overflow, panic, watchdog, startup failure, or reboot signal (`evidence/m3-m5/M3_M5_CANARY_12K_SECONDARY_STABLE_IDLE_2026-09-26.txt`, SHA-256 `06d920d5fa15a468752aeba4bff770b59153162b8964c5cc9d55ada1e94c431a`).
- 240-second directed Store launch: one physical tap emitted `pressed`, started/opened Store, then emitted `released`; Store reached the Offline network result without failure. The final minimum-free values were 7,300 / 3,600 bytes, corresponding to maximum observed stack use of 4,988 / 8,688 bytes (`evidence/m3-m5/M3_M5_CANARY_12K_SECONDARY_STORE_INTERACTION_2026-09-26.txt`, SHA-256 `61d5b9960f53279702430ea61e4b0b3496c301abb0c267b8ccbcb1b9a862f33d`).

The physical event sequence proves the probe captures real pointer input. It does not retrospectively prove the earlier delayed uncommanded opens were ghost touches, because those older images lacked the probe. Source verification confirms both configured stack size and the ESP-IDF high-water result are bytes; the tracked formal value is now 12 KiB. The clean non-diagnostic boot (`evidence/m3-m5/M3_M5_CLEAN_12K_STABLE_BOOT_2026-09-26.txt`, SHA-256 `70beabca32097210587e72857d3a5908c65e6f777dedd54dad995a4929b1f095`) and combined lifecycle (`evidence/m3-m5/M3_M5_CLEAN_COMBINED_PHYSICAL_2026-09-26.txt`, SHA-256 `8c7450759a10f404357acdae9a22db851d1039e8ed44f94c24ef5f79084a3020`) subsequently passed; remote distribution remains outside this evidence.

## Secure Transport Configuration

ESPocket 明确配置：

```text
CONFIG_BROOKESIA_SERVICE_STORAGE_ENABLE_AUTO_REGISTER=y
CONFIG_BROOKESIA_SERVICE_HTTP_ENABLE_AUTO_REGISTER=y
CONFIG_BROOKESIA_SERVICE_HTTP_ENABLE_HTTPS=y
CONFIG_BROOKESIA_SERVICE_HTTP_REQUIRE_TLS_VERIFY=y
CONFIG_BROOKESIA_SERVICE_HTTP_REQUIRE_TIME_SYNC=y
CONFIG_MBEDTLS_CERTIFICATE_BUNDLE=y
CONFIG_MBEDTLS_CERTIFICATE_BUNDLE_DEFAULT_FULL=y
```

The accepted generated `sdkconfig` and `sdkconfig.h` preserve all values above. No insecure TLS override is present: `CONFIG_ESP_TLS_INSECURE` is unset, and ESPocket does not enable `CONFIG_ESP_TLS_SKIP_SERVER_CERT_VERIFY`.

TLS protects transport and server identity. It does **not** prove publisher identity or package integrity after download.

## Package Trust Boundary

### Catalog SHA-256

Store 0.8.2 parses metadata `hash_sha256` into `StoreEntry.sha256`. Full source search finds no second read, no file SHA-256 computation, and no comparison before install.

Result: `hash_sha256` is **not enforced**.

### Core release verification

System Core 0.8.4 provides `verify_app_package_release()` with RSA-PSS-SHA256 and member hash verification. Call-site analysis shows that none of these paths invoke it:

- Store download/install;
- `SystemApi::install_runtime_app_package()`;
- `System::install_runtime_app_package()`;
- boot-time package scanning.

Result: compiling the verifier is not equivalent to enforcing it.

The required common install/discovery gate, immutable verify-to-unpack boundary, trusted reboot receipt, transactional rollback, cleanup policy, and acceptance matrix are defined in [`../design/policies/package-trust.md`](../design/policies/package-trust.md). The design is complete; enforcement remains blocked on upstream Core/Store integration and a signed ESPocket-compatible publication route.

### Runtime keyboard event isolation

Core 0.8.4 invokes a keyboard request owner's callback and then broadcasts the same `KeyboardClosed` result, including `Text`, through the service-wide `SystemCore` event. Successful Runtime stop releases all subscriptions, so the stock image and normal lifecycle do not retain a cross-App listener. However, a hostile Runtime package can subscribe, deliberately fail lifecycle `on_stop` before `Runtime::stop_app()` performs cleanup, and remain subscribed after ESPocket restores Launcher; a later Settings Wi-Fi password result could then be observed.

Current Core configuration and Runtime manifests expose no owner-scoped event authorization. ESPocket therefore applies a narrow product containment: any Runtime stop failure permanently latches keyboard input off until restart. This preserves normal Runtime execution and prevents the confirmed failure-path disclosure, but it is not a substitute for upstream owner-filtered delivery and unconditional failed-stop resource cleanup.

Result: the current product candidate is fail-closed for the reachable exception; the underlying Core isolation defect remains an upstream blocker for untrusted package distribution.

### Known official packages

Locally inspected official Calculator 0.1.0, 0.2.0, and 0.3.0 BPKs:

- declare JavaScript runtime;
- declare `systems: ["super"]`;
- contain no `META-INF/hash.json` or `META-INF/signature.sig`.

Their metadata SHA-256 values match the downloaded BPK bytes, but Store 0.8.2 does not perform that comparison.

Result: known official packages fail ESPocket system compatibility, and they cannot satisfy Core release verification as observed.

## System Compatibility

System Core uses exact system-type matching:

- missing/empty package `systems` → allowed;
- contains exact `espocket` → allowed;
- only `super` → rejected.

The Native App Store itself has no supported-system restriction and can be installed in ESPocket. Known official catalog Calculator BPKs are rejected when Core reads their manifest for `system_type="espocket"`. ESPocket will not impersonate System Super to bypass this boundary.

## Flow Status

| Flow | 状态 | 备注 |
|---|---|---|
| Store component resolve | PASS | Store 0.8.2 locked with component hash `ad0bbb0e101e79c88cf1686fe7dc27c3428e8499451ae46b5cac744845eb5036` |
| HTTP component resolve | PASS | HTTP 0.8.2 locked with component hash `501a2ccff2c76005696f513e207de6cea1abd4d2eed630c5c6ac19f5ae11cb6f` |
| Store compile/link | PASS | official Store sources compiled; final ELF/map retain Store symbols/archive |
| HTTP compile/link | PASS | HTTP static library linked; final ELF/map retain HTTP symbols/archive |
| Store resource staging/LittleFS | PASS | 17-file tree staged before image creation; LittleFS log lists Store directory/files |
| Launcher → Store → Home → Launcher | PASS (CLEAN, OFFLINE) | clean serial evidence records Store start, Offline result, and matching stop; project owner confirmed Launcher restoration |
| Remote index | PASS (PRIOR 2/2 + CURRENT 1/1, DEVICE) | official HTTPS index request submitted and `/cache/index.json` written on both request policies |
| HTTPS/TLS policy build | PASS | HTTPS, TLS verify, time sync, and full certificate bundle present in generated config |
| Initial metadata HTTPS transfer | PASS (PRIOR 2/2 IMAGE, DEVICE) | several metadata responses were written to cache; current 1/1 run did not need to repeat this to establish its later stability failure |
| Prior 2/2 concurrent HTTPS stability | FAIL (DEVICE) | 14 TLS setup failures (`-0x008D`) occurred among otherwise successful requests |
| Prior 2/2 online Store stability | FAIL (DEVICE) | one `LoadProhibited`, two `StoreProhibited`, and three automatic reboots |
| 1/1 containment app-only write | PASS (DEVICE) | only `0x60000` was written; esptool verified the written-data hash; bootloader/partition/NVS/LittleFS excluded |
| 1/1 containment clean boot | PASS (DEVICE) | one ROM banner, required app/system markers, Wi-Fi RX 10, network ready, SNTP complete, no fatal signal |
| 1/1 containment cached Store/Home | PASS (DEVICE) | matching start/open and HTTP/App stop; cached index plus five metadata files loaded; no fatal signal |
| 1/1 containment remote index/cache | PASS (DEVICE) | explicit Refresh submitted index/icon requests and wrote index cache; no `-0x008D` occurred |
| 1/1 containment online stability | FAIL (DEVICE) | connection timeout/retry then Store refresh timeout; `LoadProhibited`, `EXCVADDR=0x8`, automatic reboot; handshake stack symbolized |
| Download | BLOCKED / UNSAFE TO RETRY | a BPK request was observed, followed by panic; no compatible trusted package flow |
| Catalog SHA enforcement | BLOCKED | absent in Store 0.8.2 |
| Release signature enforcement | BLOCKED | verifier not called by install path |
| Runtime keyboard-event owner isolation | BLOCKED (UPSTREAM) | product latches keyboard off after Runtime stop failure; Core still broadcasts `KeyboardClosed.Text` globally |
| Install compatible official BPK | BLOCKED | no known official `espocket`-compatible package |
| Update | BLOCKED | requires a compatible installed package |
| Uninstall | BLOCKED | requires a compatible installed package |
| Launcher sync for downloaded apps | POLICY DEFINED / IMPLEMENTATION BLOCKED | [`../design/policies/launcher-sync.md`](../design/policies/launcher-sync.md) keeps fixed product entries separate and reconciles trusted Runtime Apps from Core; exposure stays disabled until trust and online stability gates pass |
| Public ESPocket publication path | BLOCKED | no official public route found |
| Store runtime stability | PASS (OFFLINE + CURRENT 1/1 CACHED) / FAIL (PRIOR 2/2 + CURRENT 1/1 ONLINE) | current containment passed cached Store/Home but panicked/rebooted during explicit online Refresh |
| Long-run package lifecycle stability | NOT TESTED | no compatible trusted Store flow; online Store is already device-failed before package lifecycle |

## Required Unblock

1. Consume an upstream HTTP/Store/HAL fix that serializes cancellation/timeouts with active ESP HTTP client operations, then rebuild and repeat the non-download Refresh validation. The current 1/1 containment image already failed with a symbolized TLS-handshake `LoadProhibited`; no further reproduction is required. Read-only upstream status is recorded in [`../upstream/status-2026-09-28.md`](../upstream/status-2026-09-28.md), and an unpublished Issue draft is retained at [`../upstream/issues/http-cancel-race.md`](../upstream/issues/http-cancel-race.md).
2. Obtain an official BPK whose `systems` allows `espocket`, plus a supported publication/update route.
3. Upstream Store/Core must enforce the common install and reboot-discovery trust contract defined in [`../design/policies/package-trust.md`](../design/policies/package-trust.md) before ESPocket can claim verified package distribution.
4. Upstream Core must owner-scope `KeyboardClosed` delivery and/or unconditionally release Runtime resources after lifecycle stop failure before arbitrary downloaded Runtime code can be treated as isolated.
5. Implement and device-validate [`../design/policies/launcher-sync.md`](../design/policies/launcher-sync.md) only after package trust and online HTTP stability pass; the current fixed Launcher remains the fail-closed behavior.

## Result

`BLOCKED`

Official Store source integration, exact Store/HTTP dependency resolution, clean firmware build/boot, offline Store lifecycle, TLS policy build, static security analysis, remote-index fetch, and initial HTTPS transfers are complete. The 1/1 containment image is now the current hardware image and passed app-only write verification, a clean 90-second boot, and a directed cached Store/Home lifecycle. Explicit online Refresh then proved remote-index/cache transfer without recurrence of `-0x008D`, but a later connection/retry timeout ended in a symbolized TLS-handshake `LoadProhibited` and reboot. M5 cannot become `PASS`: current containment online stability is device-failed, package verification is not enforced, Core keyboard-result events are not owner-isolated, known official packages target System Super rather than ESPocket, and no compatible publication or Launcher synchronization path is available. ESPocket's Runtime-stop-failure keyboard latch contains the demonstrated exceptional path but does not convert the upstream isolation boundary into a platform guarantee.
