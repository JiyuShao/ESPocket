"""Execute pinned HTTP retry/finish control flow with a deterministic transaction seam.

Scheduler teardown, real TLS and Store are separate device gates.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'firmware/managed_components/espressif__brookesia_service_http/src/service_http.cpp'


def method(text, start, end):
    return text[text.index(start):text.index(end, text.index(start))]


class HttpRequestTerminalTest(unittest.TestCase):
    def test_retry_cancel_and_single_terminal_result(self):
        text = SOURCE.read_text()
        actual = method(text, 'void Http::execute_request(', 'Http::HttpResponse Http::perform_request(')
        actual += method(text, 'Http::HttpResponse Http::perform_request(', 'Http::ErrorCode Http::perform_once(')
        actual += method(text, 'void Http::finish_context(', 'void Http::cleanup_finished_requests(')
        harness = r'''
#include <atomic>
#include <cassert>
#include <future>
#include <memory>
#include <mutex>
#include <string>
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS() ((void)0)
#define BROOKESIA_LOGW(...) ((void)0)
struct Http {
    enum class ErrorCode { Ok, Canceled, RequestFailed };
    enum class RequestState { Running, Completed, Failed, Canceled };
    struct HttpResponse { unsigned request_id=0; ErrorCode error=ErrorCode::Ok; int status_code=0; std::string error_message; };
    struct RequestContext { unsigned request_id=7; struct { unsigned retry_count=2; } request;
        std::atomic<bool> cancel_requested{false}; RequestState state=RequestState::Running; HttpResponse response;
        std::shared_ptr<std::promise<HttpResponse>> response_promise=std::make_shared<std::promise<HttpResponse>>(); };
    struct { unsigned completed_count=0, canceled_count=0, failed_count=0; } statistics_;
    std::mutex contexts_mutex_; unsigned running_request_count_=1, calls=0, started=0, finished=0, cleaned=0;
    int mode=0;
    void execute_request(std::shared_ptr<RequestContext>);
    HttpResponse perform_request(std::shared_ptr<RequestContext>);
    void finish_context(std::shared_ptr<RequestContext>,HttpResponse);
    void set_context_state(std::shared_ptr<RequestContext> c,RequestState state) {c->state=state;}
    void publish_request_started(const RequestContext&) {++started;}
    void publish_request_finished(const RequestContext&) {++finished;}
    void cleanup_finished_requests() {++cleaned;}
    static bool should_retry_status(const auto&,int status) {return status==503;}
    ErrorCode perform_once(std::shared_ptr<RequestContext> c,HttpResponse& r) {
        ++calls;
        if(mode==1) return ErrorCode::RequestFailed; // timeout-shaped transaction failure
        if(mode==2) {c->cancel_requested=true; return ErrorCode::Canceled;}
        if(mode==3 && calls==1) {r.status_code=503; return ErrorCode::Ok;}
        if(mode==4 && calls==1) {c->cancel_requested=true; return ErrorCode::RequestFailed;}
        r.status_code=200; return ErrorCode::Ok;
    }
};
''' + actual + r'''
int main() {
    for(int mode=0;mode<6;++mode) {
        Http http; http.mode=mode; auto c=std::make_shared<Http::RequestContext>();
        if(mode==5) c->cancel_requested=true;
        auto future=c->response_promise->get_future(); http.execute_request(c); auto response=future.get();
        assert(http.started==1 && http.finished==1 && http.cleaned==1 && http.running_request_count_==0);
        assert(http.statistics_.completed_count+http.statistics_.failed_count+http.statistics_.canceled_count==1);
        assert(!c->response_promise && response.request_id==7);
        if(mode==1) {assert(http.calls==3 && response.error==Http::ErrorCode::RequestFailed);}
        else if(mode==2 || mode==4 || mode==5) {
            assert(http.calls==(mode==5 ? 0u:1u) && response.error==Http::ErrorCode::Canceled);
            assert(c->state==Http::RequestState::Canceled);
        } else {assert(http.calls==(mode==3 ? 2u:1u) && response.error==Http::ErrorCode::Ok);}
    }
}
'''
        with tempfile.TemporaryDirectory(prefix='espocket-http-terminal-') as directory:
            source = Path(directory) / 'test.cpp'
            source.write_text(harness)
            binary = Path(directory) / 'test'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread', str(source), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=10)
