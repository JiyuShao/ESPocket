# Brookesia Upstream Blocker Status — 2026-09-28

## Status

- Scope: read-only research against official ESP Component Registry metadata and the official `espressif/esp-brookesia` repository
- Dependency changes: none
- New component downloads: none
- Build or device work: none
- `managed_components/` changes: none
- M4 and M5 remain `BLOCKED`

ESP Component Registry releases are the supported dependency baseline. Unreleased `master` is inspected only to determine whether a potential upstream fix exists; its contents are not treated as a released upgrade candidate.

## HTTP cancellation blocker

### Locked baseline

| Component | Locked version | Component hash | Registry source snapshot |
|---|---:|---|---|
| `espressif/brookesia_service_http` | 0.8.2 | `501a2ccff2c76005696f513e207de6cea1abd4d2eed630c5c6ac19f5ae11cb6f` | [`e9f22576bb4d19ca190a8105134010d514574a6b`](https://github.com/espressif/esp-brookesia/commit/e9f22576bb4d19ca190a8105134010d514574a6b) |
| `espressif/brookesia_service_helper` | 0.8.4 | `86207780be249fd45d32d0d263d011bd5415ffb61ef219ff4a70fe35b63277d7` | [`01939b5e58fd50d18339b1c35fb74c4e808962c7`](https://github.com/espressif/esp-brookesia/commit/01939b5e58fd50d18339b1c35fb74c4e808962c7) |
| `espressif/brookesia_service_manager` | 0.8.2 | `4d8d063bcb368c77de089c15f494365cf38a4f560313c583d464d58b0bd05aa2` | [`e9f22576bb4d19ca190a8105134010d514574a6b`](https://github.com/espressif/esp-brookesia/commit/e9f22576bb4d19ca190a8105134010d514574a6b) |
| `espressif/brookesia_hal_adaptor` | 0.8.4 | `e4cbe9d919117cb4d420c5b54140f81e05382243c9e1c8d8acf9aa13e2ddc75c` | [`6a087b6d76e989802b72fdb835928b273af76af8`](https://github.com/espressif/esp-brookesia/commit/6a087b6d76e989802b72fdb835928b273af76af8) |

The HTTP component's complete [Registry history](https://components.espressif.com/api/components/espressif/brookesia_service_http) contains 0.8.0, 0.8.1, and latest 0.8.2; [0.8.2](https://components.espressif.com/components/espressif/brookesia_service_http/versions/0.8.2/readme?language=en) was uploaded 2026-07-28 and is not yanked. There is no newer released HTTP-service version. HAL Adaptor 0.8.4 is likewise its latest Registry release.

The 0.8.x components are Registry releases rather than repository tags. The monorepo's public GitHub releases stop at [v0.4.2](https://github.com/espressif/esp-brookesia/releases/tag/v0.4.2), so repository release tags are not a valid inventory of current component releases.

### Current default branch

The official default branch is `master`. The inspected immutable head is [`e937455b0db1a3e873b1da61d6d13652f3dcc7e2`](https://github.com/espressif/esp-brookesia/commit/e937455b0db1a3e873b1da61d6d13652f3dcc7e2), dated 2026-09-22.

Direct Git-blob comparison gives:

| Source | Locked snapshot blob | Current `master` blob | Result |
|---|---|---|---|
| [`service_http.cpp` at locked snapshot](https://github.com/espressif/esp-brookesia/blob/e9f22576bb4d19ca190a8105134010d514574a6b/service/network/brookesia_service_http/src/service_http.cpp) / [`master` head](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/service/network/brookesia_service_http/src/service_http.cpp) | `a035589890b25fb3afbf96872b78b1b2560bd15a` | `a035589890b25fb3afbf96872b78b1b2560bd15a` | byte-identical |
| [`http_client_impl.cpp` at HAL 0.8.4 snapshot](https://github.com/espressif/esp-brookesia/blob/6a087b6d76e989802b72fdb835928b273af76af8/hal/brookesia_hal_adaptor/src/network/http_client_impl.cpp) / [current `master` head](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/hal/brookesia_hal_adaptor/src/network/http_client_impl.cpp) | `a4d83a1a5018467b222c24452bb9df618160f5d6` | `a4d83a1a5018467b222c24452bb9df618160f5d6` | byte-identical |
| Helper [`http.hpp` at locked snapshot](https://github.com/espressif/esp-brookesia/blob/01939b5e58fd50d18339b1c35fb74c4e808962c7/service/framework/brookesia_service_helper/include/brookesia/service_helper/network/http.hpp) / [`master` head](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/service/framework/brookesia_service_helper/include/brookesia/service_helper/network/http.hpp) | `5982e6dc36f4f7baefc5604ce13ce4f1e01606ed` | `5982e6dc36f4f7baefc5604ce13ce4f1e01606ed` | byte-identical; cancel remains scheduler-free |
| ServiceManager [`base.cpp` at locked snapshot](https://github.com/espressif/esp-brookesia/blob/e9f22576bb4d19ca190a8105134010d514574a6b/service/framework/brookesia_service_manager/src/service/base.cpp) / [`master` head](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/service/framework/brookesia_service_manager/src/service/base.cpp) | `54021be27227e77969821358a47690ab415acb4c` | `54021be27227e77969821358a47690ab415acb4c` | byte-identical; scheduler-free calls remain inline |

The newest returned commit touching the HTTP-service path was [`77f67b459d557a7c4f406821549037f6ef7235e4`](https://github.com/espressif/esp-brookesia/commit/77f67b459d557a7c4f406821549037f6ef7235e4), dated 2026-07-27. The newest returned commit touching HAL's HTTP-client implementation was [`6c4010f15271f81567f75ab93636ad447d40e061`](https://github.com/espressif/esp-brookesia/commit/6c4010f15271f81567f75ab93636ad447d40e061), also dated 2026-07-27. Neither path has a later source change at the inspected head.

### Race still present

The unchanged source retains this sequence:

1. Helper declares `CancelRequest.require_scheduler = false`, and ServiceManager directly invokes scheduler-free functions in the calling context.
2. `CancelRequest` sets the atomic cancellation flag and synchronously calls `close_context_transaction()` without posting cancellation to the HTTP worker or waiting for that worker.
3. `close_context_transaction()` copies the shared transaction while holding `transaction_mutex`, releases the mutex, and then calls `transaction->cancel()`.
4. The HTTP worker can concurrently execute `transaction->open()`, `read()`, or `is_complete()` without holding that mutex.
5. HAL `EspHttpTransaction::cancel()` directly calls `esp_http_client_close(client_)`; there is no operation mutex around `client_`.

The `shared_ptr` and atomic flag protect wrapper lifetime and cooperative state. They do not serialize mutation of the underlying ESP HTTP/TLS transport. The worker's assignment to raw member `client_` and cancellation's read of it are themselves unsynchronized: an early cancel can observe null and fail to interrupt the upcoming blocking open, while a later cancel can close the active handle.

The same unsafe `close_context_transaction()` boundary is reached by synchronous request wait timeout, explicit `CancelRequest`, and service `stop`/`deinit` bulk cancellation. A Store-watchdog-only patch would therefore leave sibling callers unsafe.

ESPocket is locked to [ESP-IDF v6.0.1](https://github.com/espressif/esp-idf/releases/tag/v6.0.1), commit [`8c19b156084a0753687347cca1f5355782893533`](https://github.com/espressif/esp-idf/commit/8c19b156084a0753687347cca1f5355782893533). In its [`esp_http_client.c`](https://github.com/espressif/esp-idf/blob/v6.0.1/components/esp_http_client/esp_http_client.c), close changes client state and closes the transport without a client-wide lock against another task's open/read. During HTTPS connect, the SSL transport stores an `esp_tls_t` and blocks in synchronous handshake; concurrent close destroys that object, clears the transport fields, and frees the Mbed TLS SSL/config state. This strongly supports close-during-handshake use-after-free as the observed mechanism, while the exact invalid member and instruction overlap remain unproven.

The official [ESP HTTP Client documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/esp_http_client.html) states that `esp_http_client_perform()` must not run simultaneously from two places on the same handle and identifies open/write/fetch/read/optional-close as its phases. That literal warning is attached to `perform()`, not separately repeated on every low-level API. Brookesia invokes those split phases directly, and source confirms unsynchronized mutation of the same client/transport. The existence of `esp_http_client_cancel_request()` is not evidence of a fix: Brookesia does not use it, and its ESP-IDF 6.0.1 implementation also closes and reconnects the transport without a client-wide operation mutex.

The newest of ten recent commits inspected for ESP-IDF's HTTP-client source, [`f2680c58d09c568ef45fbc9decce9052eecaf206`](https://github.com/espressif/esp-idf/commit/f2680c58d09c568ef45fbc9decce9052eecaf206), fixes read-timeout truncation rather than close/cancel synchronization.

### Public issue/PR search

Targeted public searches using HTTP, cancel, `esp_http_client`, TLS, race, concurrency, synchronization, scheduler, crash, and worker terms found no record claiming this fix. [PR #114](https://github.com/espressif/esp-brookesia/pull/114) concerns scheduler waiting-worker quotas and unrelated cancellation cleanup; [Issue #102](https://github.com/espressif/esp-brookesia/issues/102) concerns a Boost.Asio scheduler-startup race. Neither changes the byte-identical HTTP blobs above.

Anonymous API results were incomplete: 17 Issue records, 6 PR records, and 7 of 54 broad-search matches were exposed. This is therefore “no public fix evidence found,” not proof that no private or unindexed discussion exists. The released-version inventory and direct immutable-source comparison do not depend on that search limitation.

### Conclusion

No confirmed official fix exists in a released component or at the inspected current `master` head. The locked HTTP service is already the latest Registry release, and all four decisive service, HAL, Helper-schema, and ServiceManager-dispatch source files are byte-identical to current `master`. The one-worker/one-request ESPocket setting mitigates overlapping TLS allocation pressure but cannot serialize cancellation from the Store/System context against the active worker. The upstream `deterministic_async_cancel` test waits only for `RequestStarted`, which is published before `open()`; it does not force or assert a close-versus-open/read overlap.

Keep M5 online Store stability blocked. The source-backed failure report remains an unpublished draft at [`issues/http-cancel-race.md`](2026-09-28-http-cancel-race.md); no upstream Issue was submitted.

## Audio playback-only blocker

### Locked baseline

| Component | Locked version | Component hash | Registry source snapshot |
|---|---:|---|---|
| `espressif/brookesia_hal_adaptor` | 0.8.4 | `e4cbe9d919117cb4d420c5b54140f81e05382243c9e1c8d8acf9aa13e2ddc75c` | [`6a087b6d76e989802b72fdb835928b273af76af8`](https://github.com/espressif/esp-brookesia/commit/6a087b6d76e989802b72fdb835928b273af76af8) |
| `espressif/brookesia_service_audio` | 0.8.2 | `fa2c42fa777aad7b2f5b8dab3829c7e2448fd211f3dc29418eb1353662e53afc` | [`e9f22576bb4d19ca190a8105134010d514574a6b`](https://github.com/espressif/esp-brookesia/commit/e9f22576bb4d19ca190a8105134010d514574a6b) |

The lock and each installed component's `repository_info.commit_sha` establish these exact identities.

### Released upstream state

- HAL Adaptor latest remains [0.8.4](https://components.espressif.com/components/espressif/brookesia_hal_adaptor/versions/0.8.4/changelog?language=en), uploaded 2026-08-27; complete Registry history: [component API](https://components.espressif.com/api/components/espressif/brookesia_hal_adaptor).
- Audio service latest remains [0.8.2](https://components.espressif.com/components/espressif/brookesia_service_audio/versions/0.8.2/changelog?language=en), uploaded 2026-07-28; complete Registry history: [component API](https://components.espressif.com/api/components/espressif/brookesia_service_audio).
- No newer released version exists for either component.

### Current default branch

The official default branch is `master`. The inspected immutable head is [`e937455b0db1a3e873b1da61d6d13652f3dcc7e2`](https://github.com/espressif/esp-brookesia/commit/e937455b0db1a3e873b1da61d6d13652f3dcc7e2), dated 2026-09-22.

At that head:

- [HAL Kconfig](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/hal/brookesia_hal_adaptor/Kconfig) still makes Audio Processor depend on both Codec Player and Codec Recorder.
- [HAL CMake](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/hal/brookesia_hal_adaptor/CMakeLists.txt) can compile the lower-level codec-player implementation independently, but compiles the processor and its `av_processor` dependency only when Audio Processor is enabled.
- [HAL device registration](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/hal/brookesia_hal_adaptor/src/audio/device.cpp) exposes `CodecPlayerIface` for the codec player but exposes the higher-level `PlaybackIface` only through Audio Processor.
- [AudioPlayback](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/service/media/brookesia_service_audio/src/audio_playback.cpp) still requires `PlaybackIface` on start.
- The [Audio-service Kconfig](https://github.com/espressif/esp-brookesia/blob/e937455b0db1a3e873b1da61d6d13652f3dcc7e2/service/media/brookesia_service_audio/Kconfig) exposes no recorder-disable or playback-only backend switch.

The post-release dependency commit [`814318c799c6ba0b4803fad3540e3cddc153e277`](https://github.com/espressif/esp-brookesia/commit/814318c799c6ba0b4803fad3540e3cddc153e277), dated 2026-09-21, changes `esp_video` dependency matching. It does not remove the processor's player-and-recorder Kconfig dependency or make `PlaybackIface` available from a codec player alone.

### Public issue/PR search

No matching item surfaced in a search of the latest 100 all-state public GitHub Issues/PRs using audio, playback, player, recorder, processor, `av_processor`, Kconfig, and dependency terms. [Issue #111](https://github.com/espressif/esp-brookesia/issues/111) concerns `esp_player`/seek capability and is not this configuration problem. This search result is supporting evidence; the no-fix conclusion comes from the released-version inventory and direct inspection of the immutable current source.

### Conclusion

No official released or current-`master` fix exists. A bare HAL codec player is independently selectable, but it does not satisfy the `PlaybackIface` contract used by the official Audio service and Settings Sound/Volume flow. Enabling recorder remains the only official path to the processor-backed interface, which violates ESPocket's playback-only product boundary.

Keep M4 Sound/Volume blocked. Do not enable recorder, patch or vendor the managed component, or replace the official Audio-service stack with an ESPocket-private framework.
