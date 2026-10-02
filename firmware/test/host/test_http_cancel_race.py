"""Run the actual ESP HAL transaction with deterministic open/read barriers."""
import os
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[3]
HAL = ROOT / 'firmware/managed_components/espressif__brookesia_hal_adaptor'
BOOST = ROOT / 'firmware/managed_components/espressif__esp-boost/src'

class HttpCancelRaceTest(unittest.TestCase):
    def test_cancel_does_not_close_an_active_handle(self):
        sys.path.insert(0, str(ROOT / 'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='espocket-http-copy-') as directory:
            patched = prepare(HAL, ROOT / 'firmware/patches/espressif__brookesia_hal_adaptor/0.8.4/manifest.json',
                              Path(directory) / 'patched')
            original = self.exercise(HAL)
            self.assertNotEqual(original.returncode, 0)
            self.assertIn('cancel closed HTTP handle during active operation', original.stderr)
            fixed = self.exercise(patched)
            self.assertEqual(fixed.returncode, 0, fixed.stderr)

    def exercise(self, hal):
        text = (hal / 'src/network/http_client_impl.cpp').read_text()
        transaction = text[text.index('class EspHttpTransaction:'):text.index('} // namespace')]
        harness = r'''
#include <algorithm>
#include <atomic>
#include <boost/json.hpp>
#include <condition_variable>
#include <expected>
#include <future>
#include <mutex>
#include <string>
#include <thread>
#include <vector>
#include <iostream>
struct Barrier { std::mutex mutex; std::condition_variable condition;
    bool entered = false, released = false; int operation = 0; std::atomic<bool> active{false}, overlap{false};
    void run(int selected) { if (operation != selected) return;
        std::unique_lock lock(mutex); active = true; entered = true; condition.notify_all();
        condition.wait(lock, [&]{return released;}); active = false;
    }
    void wait() { std::unique_lock lock(mutex); condition.wait(lock,[&]{return entered;}); }
    void release() { std::lock_guard lock(mutex); released = true; condition.notify_all(); }
} barrier;
using esp_err_t = int; constexpr int ESP_OK = 0, HTTP_EVENT_ON_HEADER = 1;
using esp_http_client_handle_t = int*;
struct esp_http_client_event_t { int event_id; void* user_data; const char* header_key; const char* header_value; };
struct esp_http_client_config_t { const char* url; unsigned timeout_ms; int buffer_size_tx;
    bool disable_auto_redirect, skip_cert_common_name_check; esp_err_t(*event_handler)(esp_http_client_event_t*);
    void* user_data; const char* cert_pem; int(*crt_bundle_attach)(void*); };
int esp_crt_bundle_attach(void*) { return 0; }
int handle_storage;
esp_http_client_handle_t esp_http_client_init(esp_http_client_config_t*) { return &handle_storage; }
int esp_http_client_cleanup(esp_http_client_handle_t) { if(barrier.active) barrier.overlap = true; return 0; }
int esp_http_client_close(esp_http_client_handle_t) { if(barrier.active) barrier.overlap = true; return 0; }
int esp_http_client_set_method(esp_http_client_handle_t, int) { return 0; }
int esp_http_client_set_header(esp_http_client_handle_t,const char*,const char*) { return 0; }
int esp_http_client_open(esp_http_client_handle_t,int) { barrier.run(1); return 0; }
int esp_http_client_write(esp_http_client_handle_t,const char*,int length) { return length; }
int esp_http_client_fetch_headers(esp_http_client_handle_t) { return 0; }
int esp_http_client_get_status_code(esp_http_client_handle_t) { return 200; }
int esp_http_client_read(esp_http_client_handle_t,char*,size_t) { barrier.run(2); return 0; }
bool esp_http_client_is_complete_data_received(esp_http_client_handle_t) { return true; }
const char* esp_err_to_name(int) { return "error"; }
#define BROOKESIA_HAL_ADAPTOR_NETWORK_HTTP_CLIENT_REQUIRE_TLS_VERIFY 1
#define BROOKESIA_HAL_ADAPTOR_NETWORK_HTTP_CLIENT_TX_BUFFER_SIZE 1024
namespace network { struct HttpClientIface {
    enum class ErrorCode { Ok, ClientInitFailed, RequestFailed, Canceled };
    enum class TlsVerifyMode { Default, Verify };
    struct Request { std::string url="https://example.invalid/"; int method=0;
        unsigned timeout_ms=100; TlsVerifyMode tls_verify = TlsVerifyMode::Verify;
        std::string cert_pem, body; bool use_crt_bundle = true; boost::json::object headers; };
    struct Response { std::string error_message; int status_code=0; boost::json::object headers; };
    struct Transaction { virtual ~Transaction()=default;
        virtual ErrorCode open(const Request&,Response&,uint32_t&)=0;
        virtual int read(char*,size_t,std::string&)=0;
        virtual bool is_complete() const=0;
        virtual void cancel()=0;
    };
}; }
using ErrorCode = network::HttpClientIface::ErrorCode;
using Request = network::HttpClientIface::Request;
using Response = network::HttpClientIface::Response;
using TlsVerifyMode = network::HttpClientIface::TlsVerifyMode;
bool is_https_url(const std::string&) { return true; }
int to_esp_method(int value) { return value; }
std::string json_value_to_header_string(const boost::json::value& value) { return boost::json::serialize(value); }
''' + transaction + r'''
int main() {
    for (int operation : {1, 2}) {
        barrier.operation = operation; barrier.entered = false; barrier.released = false; barrier.overlap = false;
        EspHttpTransaction transaction; Request request; Response response; uint32_t length=0;
        if (operation==2) { barrier.operation=0; transaction.open(request,response,length); barrier.operation=2; }
        auto worker = std::async(std::launch::async,[&] {
            if(operation==1) transaction.open(request,response,length);
            else { char buffer[4]; std::string error; transaction.read(buffer,4,error); }
        });
        barrier.wait();
        transaction.cancel(); // active owner worker is deliberately blocked inside the client
        bool overlap = barrier.overlap;
        barrier.release(); worker.get();
        if(overlap) { std::cerr << "FAIL: cancel closed HTTP handle during active operation\n"; return 1; }
        if(transaction.is_complete()) { std::cerr << "FAIL: canceled transaction reported complete\n"; return 2; }
    }
}
'''
        with tempfile.TemporaryDirectory(prefix='espocket-http-cancel-') as directory:
            source=Path(directory)/'test.cpp';source.write_text(harness)
            boost=Path(directory)/'boost.cpp';boost.write_text('#include <boost/json/src.hpp>\n')
            binary=Path(directory)/'test'
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23','-pthread','-DBOOST_NO_USER_CONFIG',
                            '-I',str(BOOST),str(source),str(boost),'-o',str(binary)],check=True)
            return subprocess.run([str(binary)],text=True,capture_output=True,timeout=10)
