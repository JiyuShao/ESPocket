# Issue draft: `CancelRequest` can close an ESP HTTP client during an active TLS handshake

> Draft only. This document has not been published or submitted upstream.
>
> Official Registry/current-`master` status was rechecked on 2026-09-28 in [`../status-2026-09-28.md`](2026-09-28-upstream-status.md); no confirmed fix was found.

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

The sanitized symbolized crashing-task stack was generated from ELF SHA-256 `cc40c08b4da608962624f7dd4daa4e455a8a3e5efaefa149495a4fe7c8f770e1`. Local absolute prefixes were normalized to `ESP-IDF/`, `managed_components/`, and `toolchain/`; addresses, symbols, source-relative paths, line numbers, and inlining notes are unchanged:

```text
0x423379e9: mbedtls_ssl_handshake_step at ESP-IDF/components/mbedtls/mbedtls/library/ssl_tls.c:4158
 (inlined by) mbedtls_ssl_handshake_step at ESP-IDF/components/mbedtls/mbedtls/library/ssl_tls.c:4110
0x42337a24: mbedtls_ssl_handshake at ESP-IDF/components/mbedtls/mbedtls/library/ssl_tls.c:4222
 (inlined by) mbedtls_ssl_handshake at ESP-IDF/components/mbedtls/mbedtls/library/ssl_tls.c:4199
0x4239c91d: esp_mbedtls_handshake at ESP-IDF/components/esp-tls/esp_tls_mbedtls.c:280
0x4239bf79: esp_tls_handshake at ESP-IDF/components/esp-tls/esp_tls.c:130
0x4239c192: esp_tls_low_level_conn at ESP-IDF/components/esp-tls/esp_tls.c:540
0x4239c2c5: esp_tls_conn_new_sync at ESP-IDF/components/esp-tls/esp_tls.c:571
0x4239d6dc: ssl_connect at ESP-IDF/components/tcp_transport/transport_ssl.c:118 (discriminator 1)
0x423e98fd: esp_transport_connect at ESP-IDF/components/tcp_transport/transport.c:123
0x42333e65: esp_http_client_connect at ESP-IDF/components/esp_http_client/esp_http_client.c:1686
0x423348ca: esp_http_client_open at ESP-IDF/components/esp_http_client/esp_http_client.c:1868
0x420cca67: esp_brookesia::hal::(anonymous namespace)::EspHttpTransaction::open(esp_brookesia::hal::network::HttpClientIface::Request const&, esp_brookesia::hal::network::HttpClientIface::Response&, unsigned long&) at managed_components/espressif__brookesia_hal_adaptor/src/network/http_client_impl.cpp:146
0x42098f0f: esp_brookesia::service::http::Http::perform_once(std::shared_ptr<esp_brookesia::service::http::Http::RequestContext>, esp_brookesia::hal::network::HttpClientIface::Response&) at managed_components/espressif__brookesia_service_http/src/service_http.cpp:481 (discriminator 1)
0x42099292: esp_brookesia::service::http::Http::perform_request(std::shared_ptr<esp_brookesia::service::http::Http::RequestContext>) at managed_components/espressif__brookesia_service_http/src/service_http.cpp:430 (discriminator 1)
0x42099d55: esp_brookesia::service::http::Http::execute_request(std::shared_ptr<esp_brookesia::service::http::Http::RequestContext>) at managed_components/espressif__brookesia_service_http/src/service_http.cpp:409 (discriminator 1)
0x42099e1b: esp_brookesia::service::http::Http::submit_request[abi:cxx11](esp_brookesia::hal::network::HttpClientIface::Request, std::shared_ptr<std::promise<esp_brookesia::hal::network::HttpClientIface::Response> >)::{lambda()#1}::operator()() const at managed_components/espressif__brookesia_service_http/src/service_http.cpp:378 (discriminator 1)
0x42099e45: std::_Function_handler<void (), esp_brookesia::service::http::Http::submit_request[abi:cxx11](esp_brookesia::hal::network::HttpClientIface::Request, std::shared_ptr<std::promise<esp_brookesia::hal::network::HttpClientIface::Response> >)::{lambda()#1}>::_M_invoke(std::_Any_data const&) at toolchain/xtensa-esp-elf/include/c++/15.2.0/bits/invoke.h:63
 (inlined by) __invoke_r<void, esp_brookesia::service::http::Http::submit_request(HttpRequest, std::shared_ptr<std::promise<esp_brookesia::hal::network::HttpClientIface::Response> >)::<lambda()>&> at toolchain/xtensa-esp-elf/include/c++/15.2.0/bits/invoke.h:113
 (inlined by) _M_invoke at toolchain/xtensa-esp-elf/include/c++/15.2.0/bits/std_function.h:292
0x420699c2: std::function<void ()>::operator()() const at toolchain/xtensa-esp-elf/include/c++/15.2.0/bits/std_function.h:593
0x422db94f: esp_brookesia::lib_utils::TaskScheduler::Impl::post_internal(std::function<void ()>, unsigned long long*, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, bool)::{lambda()#1}::operator()() const at managed_components/espressif__brookesia_lib_utils/src/task_scheduler.cpp:301
0x422dba1e: boost::asio::detail::executor_op<boost::asio::detail::binder0<esp_brookesia::lib_utils::TaskScheduler::Impl::post_internal(std::function<void ()>, unsigned long long*, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, bool)::{lambda()#1}>, std::allocator<void>, boost::asio::detail::scheduler_operation>::do_complete(void*, boost::asio::detail::scheduler_operation*, boost::system::error_code const&, unsigned int) at managed_components/espressif__esp-boost/src/boost/asio/detail/bind_handler.hpp:56
 (inlined by) do_complete at managed_components/espressif__esp-boost/src/boost/asio/detail/executor_op.hpp:70
0x422d5c09: boost::asio::detail::scheduler_operation::complete(void*, boost::system::error_code const&, unsigned int) at managed_components/espressif__esp-boost/src/boost/asio/detail/scheduler_operation.hpp:40
 (inlined by) boost::asio::detail::scheduler::do_poll_one(boost::asio::detail::conditionally_enabled_mutex::scoped_lock&, boost::asio::detail::scheduler_thread_info&, boost::system::error_code const&) at managed_components/espressif__esp-boost/src/boost/asio/detail/impl/scheduler.ipp:641
0x422d634a: boost::asio::detail::scheduler::poll(boost::system::error_code&) at managed_components/espressif__esp-boost/src/boost/asio/detail/impl/scheduler.ipp:275 (discriminator 2)
0x422d6b6d: boost::asio::io_context::poll() at managed_components/espressif__esp-boost/src/boost/asio/impl/io_context.ipp:87
0x422da61d: esp_brookesia::lib_utils::TaskScheduler::Impl::start(esp_brookesia::lib_utils::TaskSchedulerStartConfig const&)::{lambda()#2}::operator()() const at managed_components/espressif__brookesia_lib_utils/src/task_scheduler.cpp:182 (discriminator 1)
0x422da696: boost::detail::thread_data<esp_brookesia::lib_utils::TaskScheduler::Impl::start(esp_brookesia::lib_utils::TaskSchedulerStartConfig const&)::{lambda()#2}>::run() at managed_components/espressif__esp-boost/src/boost/thread/detail/thread.hpp:120
0x422f93c6: thread_proxy at managed_components/espressif__esp-boost/src/boost/thread/src/pthread/thread.cpp:177 (discriminator 1)
0x42009db0: pthread_task_func at ESP-IDF/components/pthread/pthread.c:241
0x423f525e: vPortTaskWrapper at ESP-IDF/components/freertos/FreeRTOS-Kernel/portable/xtensa/port.c:143
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
