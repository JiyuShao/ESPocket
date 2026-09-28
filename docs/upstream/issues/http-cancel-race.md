# Issue draft: `CancelRequest` can close an ESP HTTP client during an active TLS handshake

> Draft only. This document has not been published or submitted upstream.
>
> Official Registry/current-`master` status was rechecked on 2026-09-28 in [`../status-2026-09-28.md`](../status-2026-09-28.md); no confirmed fix was found.

## Summary

`brookesia_service_http` cancellation can call `esp_http_client_close()` from a service caller context while the HTTP worker is still using the same client in `esp_http_client_open()`, `esp_http_client_read()`, or `esp_http_client_is_complete_data_received()`.

On ESP32-S3, an App Store refresh watchdog canceled a timed-out request while the only HTTP worker was in the retry attempt's TLS handshake. The worker immediately panicked with `LoadProhibited` (`EXCVADDR=0x00000008`) and rebooted. The symbolized crashing-task stack starts in `mbedtls_ssl_handshake_step()` and continues through `esp_http_client_open()` and the Brookesia HTTP worker.

The source contains a confirmed unsupported same-handle concurrency path. Close-versus-handshake invalidation is the strongest and most likely explanation for this panic, but the capture does not include the canceling task's stack inside `esp_http_client_close()`. The precise two-task instruction overlap and exact invalid Mbed TLS member therefore remain strongly supported rather than instruction-for-instruction proven.

## Affected configuration

- Target: ESP32-S3
- ESP-IDF: 6.0.1
- Mbed TLS: 4.0.0 (bundled with ESP-IDF 6.0.1)
- `espressif/brookesia_service_http`: 0.8.2, Registry component hash `501a2ccff2c76005696f513e207de6cea1abd4d2eed630c5c6ac19f5ae11cb6f`
- `espressif/brookesia_service_helper`: 0.8.4, Registry component hash `86207780be249fd45d32d0d263d011bd5415ffb61ef219ff4a70fe35b63277d7`
- `espressif/brookesia_service_manager`: 0.8.2, Registry component hash `4d8d063bcb368c77de089c15f494365cf38a4f560313c583d464d58b0bd05aa2`
- `espressif/brookesia_hal_adaptor`: 0.8.4, Registry component hash `e4cbe9d919117cb4d420c5b54140f81e05382243c9e1c8d8acf9aa13e2ddc75c`
- `espressif/brookesia_app_store`: 0.8.2, Registry component hash `ad0bbb0e101e79c88cf1686fe7dc27c3428e8499451ae46b5cac744845eb5036`
- HTTPS certificate verification and required time synchronization enabled
- HTTP worker count: 1
- Maximum concurrent requests: 1
- Request timeout: 15,000 ms
- Retry count: 1
- App Store watchdog: `15000 * (1 + 1) + 1000 = 31,000 ms`

Using one worker and one maximum concurrent request prevents inter-request TLS allocation overlap. It does not serialize cancellation from the App/System worker with the active HTTP worker transaction.

## Steps that triggered the failure

1. Boot the ESP32-S3 system with the official App Store and HTTP service.
2. Wait for Wi-Fi and SNTP readiness.
3. Open App Store and use its header Refresh action.
4. Allow the remote index connection to time out so the HTTP service starts its configured retry.
5. Let the App Store's 31-second refresh watchdog cancel the request while the retry attempt remains in TLS setup.

A stalled endpoint or fault-injection test that keeps `esp_http_client_open()` active while another service context calls `CancelRequest` should exercise the same concurrency boundary more deterministically.

## Actual result

The request was submitted at 83,969 ms. Its first connection attempt timed out at 100,712 ms, and the HTTP service immediately announced a retry. At 114,986 ms—31,017 ms after submission—the App Store watchdog logged the request timeout. A `LoadProhibited` followed immediately:

```text
I (83969) SvcHTTP: Submitted HTTP request: id(3), url(.../api/v1/index.json)
W (100712) esp-tls: Failed to open new connection in specified timeout
W (100722) SvcHTTP: HTTP request 3 failed on attempt 1: error(RequestFailed), message(ESP_ERR_HTTP_CONNECT), retrying
W (114986) AppStore: App Store refresh request timeout: request_id(3)
Guru Meditation Error: Core 0 panic'ed (LoadProhibited)
PC      : 0x423379ec
EXCVADDR: 0x00000008
```

The exact firmware identities were:

```text
App image SHA-256: 870c7031dfa64dd20347d0879e3753608df37365973a07b609c2697ca98cf72b
ELF SHA-256:       cc40c08b4da608962624f7dd4daa4e455a8a3e5efaefa149495a4fe7c8f770e1
Panic ELF prefix:  cc40c08b4
```

The symbolized crashing-task stack was:

```text
mbedtls_ssl_handshake_step
mbedtls_ssl_handshake
esp_mbedtls_handshake
esp_tls_handshake
esp_tls_low_level_conn
esp_tls_conn_new_sync
ssl_connect
esp_transport_connect
esp_http_client_connect
esp_http_client_open
EspHttpTransaction::open
Http::perform_once
Http::perform_request
Http::execute_request
HTTP scheduler closure
TaskScheduler / Boost.Asio / pthread / FreeRTOS
```

The device rebooted automatically. No matching App Store stop occurred before the panic.

## Expected result

`CancelRequest` should safely move the request to a canceled terminal state without operating on an `esp_http_client` handle concurrently with its active `open`, `read`, or completion-check operation. A timeout during TLS setup must not panic or reboot the device.

## Source-level concurrency path

The locked 0.8.2/0.8.4 source has the following sequence:

1. App Store's refresh watchdog calls `CancelRequest` from its timeout handler.
2. The Helper schema declares `CancelRequest.require_scheduler = false`; ServiceManager therefore invokes it directly in the calling context instead of posting it to the HTTP scheduler.
3. `Http::function_cancel_request()` sets `cancel_requested` and calls `close_context_transaction()`.
4. `close_context_transaction()` copies the shared transaction under `transaction_mutex`, releases the mutex, then calls `transaction->cancel()`.
5. The HTTP worker publishes the transaction before entering `transaction->open()`, and it does not hold `transaction_mutex` across `open()`, `read()`, or `is_complete()`.
6. ESP HAL implements `EspHttpTransaction::cancel()` as `esp_http_client_close(client_)`; `client_` and its operations have no mutex or atomic synchronization.

Relevant source excerpts:

```cpp
// brookesia_service_helper/include/brookesia/service_helper/network/http.hpp
{
    .name = "CancelRequest",
    // ...
    .require_scheduler = false,
},
```

```cpp
// brookesia_service_manager/src/service/base.cpp
if (!require_scheduler) {
    call_function_task();
    return true;
}
```

```cpp
// brookesia_service_http/src/service_http.cpp
context->cancel_requested.store(true);
close_context_transaction(*context);
```

```cpp
// brookesia_service_http/src/service_http.cpp
std::shared_ptr<HttpTransaction> transaction;
{
    std::lock_guard<std::mutex> lock(context.transaction_mutex);
    transaction = context.transaction;
}
if (transaction != nullptr) {
    transaction->cancel();
}
```

```cpp
// brookesia_service_http/src/service_http.cpp
set_context_transaction(*context, transaction);
// ...
auto error = transaction->open(request, response, content_length);
```

```cpp
// brookesia_hal_adaptor/src/network/http_client_impl.cpp
void EspHttpTransaction::cancel()
{
    if (client_ != nullptr) {
        esp_http_client_close(client_);
    }
}
```

Shared ownership keeps the C++ transaction wrapper alive, but it does not serialize mutation of the underlying ESP HTTP client/TLS state. There is also a direct unsynchronized access to the HAL member itself: `open()` writes `client_ = esp_http_client_init(...)` while `cancel()` may read `client_`. An early cancellation can therefore observe null and become a no-op while the blocking open continues; a later cancellation can close the active handle.

ESP-IDF documents that `esp_http_client_perform()` must never run simultaneously from two places on the same handle and identifies `open`, `write`, `fetch_headers`, `read`, and optional `close` as phases of that operation. The warning is attached to `perform()` rather than separately repeated on every low-level API. Brookesia invokes those low-level phases directly, and the ESP-IDF implementation confirms they mutate the same handle and transport without a client-wide lock.

During HTTPS connect, `ssl_connect()` stores a newly allocated `esp_tls_t` in the transport and blocks in `esp_tls_conn_new_sync()`. A concurrent `esp_http_client_close()` reaches the SSL transport's close callback, which calls `esp_tls_conn_destroy()` on that same object, clears the transport fields, and frees the Mbed TLS configuration and SSL context. This makes close-during-handshake use-after-free the strongest source-supported mechanism for the observed `mbedtls_ssl_handshake_step()` crash. The capture still does not identify the exact freed member or prove the precise two-task instruction overlap.

The unsafe helper is also reached by the synchronous request wait timeout and service `stop`/`deinit` bulk cancellation, so the defect is not limited to App Store refresh or explicit `CancelRequest`. Fixing only the Store watchdog would leave the shared HTTP boundary unsafe.

## Suggested fix requirements

Please ensure that cancellation/timeout handling cannot close or mutate a client while its owning worker is inside an operation on that same handle. Possible implementations may differ, but the invariant should be:

```text
For one HttpTransaction, open/write/fetch/read/completion/close/cancel operations
must not execute concurrently on the underlying esp_http_client handle.
```

The existing `deterministic_async_cancel` test waits for `RequestStarted` and then cancels a delayed request. `RequestStarted` is published before `perform_request()` enters `open()`, so the test neither forces nor asserts a close-versus-open/read overlap.

A race regression should instead:

1. add a deterministic test barrier/hook after `Transaction::open()` has entered but before it returns, and separately after response `read()` has entered;
2. block the active operation at that barrier;
3. issue `CancelRequest` from a second task/service context;
4. assert that `cancel()` or the underlying close cannot overlap the in-flight client operation;
5. release the barrier and require exactly one canceled terminal event;
6. reject panic, reboot, use-after-close, double completion, or a late success event.

Repeated on-device stress remains useful supplemental coverage but is not a deterministic regression. The test should cover explicit cancellation, synchronous timeout, and stop/deinit bulk cancellation under both one-worker/one-request and multi-worker configurations. Merely reducing worker count is not sufficient because cancellation originates outside the active request worker.

## Evidence

Public-shareable repository evidence:

- `docs/milestones/evidence/m5/M5_HTTP_SERIAL_CONTAINMENT_ONLINE_FAILURE_2026-09-27.txt`
  - SHA-256: `83060cddcfaa729895d38f845cb7908585c22c39c3638ed13fe8b74be80f02e5`
- `docs/upstream/issues/evidence/http-cancel-race-stack-sanitized.txt`
  - SHA-256: `b70b88c444b3680071202ded7305f04a76894cdc2f5db49bd63b4649b359c150`
  - Exact symbolized stack with only local absolute path prefixes replaced by `ESP-IDF/`, `managed_components/`, and `toolchain/`.
- `docs/milestones/evidence/m5/M5_HTTP_SERIAL_CONTAINMENT_ONLINE_FAILURE_SUMMARY_2026-09-27.txt`
  - SHA-256: `e1c5c5399d11681fda2c53f4c00bf8ca55e8a9474b8971ad7a199abc8826f24f`

The public-shareable files exclude Wi-Fi credentials, SSID/BSSID values, MAC addresses, and local usernames or absolute build paths. The original internal symbolization evidence remains immutable for acceptance provenance and is not intended as a public attachment.
