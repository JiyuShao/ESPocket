"""WiFi start keeps default power policy; product opt-in applies before start."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class WifiLowLatencyTest(unittest.TestCase):
    def test_actual_start_order_and_errors(self):
        with tempfile.TemporaryDirectory(prefix='wifi-low-latency-') as directory:
            temporary = Path(directory)
            component = prepare(ROOT / 'firmware/managed_components/espressif__brookesia_hal_adaptor',
                                ROOT / 'firmware/patches/espressif__brookesia_hal_adaptor/0.8.4/manifest.json',
                                temporary / 'component')
            source = (component / 'src/wifi/backend.cpp').read_text()
            start = source.index('bool WifiEspBackend::do_start()')
            method = source[start:source.index('\n}\n', start) + 3]
            device = (component / 'src/wifi/device.cpp').read_text()
            start = device.index('bool WifiDevice::set_low_latency(bool enabled)')
            configure = device[start:device.index('\n}\n', start) + 3]
            code = r'''
#include <cassert>
#include <vector>
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS()
#define BROOKESIA_LOGI(...)
#define BROOKESIA_CHECK_ESP_ERR_RETURN(call, fallback, ...) if ((call)!=0) return fallback;
#define BROOKESIA_CHECK_FALSE_RETURN(value, fallback, ...) if (!(value)) return fallback;
constexpr int WIFI_MODE_STA=1, WIFI_PS_NONE=0;
std::vector<int> calls;
int failed=0;
int esp_wifi_set_mode(int mode){assert(mode==WIFI_MODE_STA);calls.push_back(1);return failed==1;}
int esp_wifi_set_ps(int mode){assert(mode==WIFI_PS_NONE);calls.push_back(2);return failed==2;}
int esp_wifi_start(){calls.push_back(3);return failed==3;}
struct WifiEspBackend {bool low_latency_=false;bool do_start();};
struct WifiDevice {
    bool low_latency_=false, initialized=false;
    static constexpr const char* BASIC_IFACE_NAME="WiFi:Basic";
    bool is_iface_initialized(const char*)const{return initialized;}
    bool set_low_latency(bool enabled);
};
''' + method + configure + r'''
int main(){
    WifiDevice device;
    assert(device.set_low_latency(true));assert(device.low_latency_);
    device.initialized=true;
    assert(!device.set_low_latency(false));assert(device.low_latency_);
    WifiEspBackend backend;
    assert(backend.do_start());assert((calls==std::vector<int>{1,3}));
    backend.low_latency_=true;calls.clear();
    assert(backend.do_start());assert((calls==std::vector<int>{1,2,3}));
    for(int error=1;error<=3;error++){
        failed=error;calls.clear();assert(!backend.do_start());
        assert(calls.size()==static_cast<unsigned>(error));
    }
}
'''
            fixture = temporary / 'test.cpp'
            fixture.write_text(code)
            binary = temporary / 'test'
            subprocess.run([os.environ.get('CXX', 'c++'), '-std=c++17', str(fixture), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
