"""Exercise the production Developer Mode package-policy retry state machine."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 'firmware/components/espocket_system/src/system_power.cpp'


class RuntimePackagePolicyRetryTest(unittest.TestCase):
    def test_stop_failure_backoff_recovery_and_reenable(self):
        source = SOURCE.read_text()
        start = source.index('void System::tick_runtime_package_policy(')
        end = source.index('\nvoid System::poll_system_input()', start)
        method = source[start:end]
        harness = r'''
#include <algorithm>
#include <cassert>
#include <cinttypes>
#include <cstdint>
#include <expected>
#include <string>
#define ESP_LOGE(...) ((void)0)
constexpr const char *TAG = "test";
namespace espocket {
struct System {
    bool package_developer_was_enabled_ = true;
    uint64_t package_policy_retry_at_ms_ = 0;
    uint32_t package_policy_retry_delay_ms_ = 1000;
    unsigned attempts = 0;
    unsigned failures = 0;
    std::expected<void, std::string> enforce_runtime_package_policy() {
        ++attempts;
        if (failures) { --failures; return std::unexpected("stop failure"); }
        return {};
    }
    void tick_runtime_package_policy(bool developer_enabled, uint64_t now_ms);
};
''' + method + r'''
}
int main() {
    espocket::System system;
    system.failures = 6;
    system.tick_runtime_package_policy(false, 100);
    assert(system.attempts == 1 && system.package_policy_retry_at_ms_ == 1100);
    for (uint64_t now : {101, 1099}) system.tick_runtime_package_policy(false, now);
    assert(system.attempts == 1);
    system.tick_runtime_package_policy(false, 1100);
    assert(system.attempts == 2 && system.package_policy_retry_at_ms_ == 3100);
    system.tick_runtime_package_policy(false, 3100);
    system.tick_runtime_package_policy(false, 7100);
    system.tick_runtime_package_policy(false, 15100);
    system.tick_runtime_package_policy(false, 31100);
    assert(system.attempts == 6 && system.package_policy_retry_delay_ms_ == 30000);
    system.tick_runtime_package_policy(false, 61099);
    assert(system.attempts == 6);
    system.tick_runtime_package_policy(false, 61100);
    assert(system.attempts == 7 && !system.package_developer_was_enabled_);
    system.tick_runtime_package_policy(false, 100000);
    assert(system.attempts == 7);
    system.tick_runtime_package_policy(true, 100001);
    assert(system.package_developer_was_enabled_ && system.package_policy_retry_delay_ms_ == 1000);
    system.tick_runtime_package_policy(false, 100002);
    assert(system.attempts == 8 && !system.package_developer_was_enabled_);
}
'''
        with tempfile.TemporaryDirectory(prefix='espocket-package-policy-') as directory:
            cpp = Path(directory) / 'test.cpp'
            binary = Path(directory) / 'test'
            cpp.write_text(harness)
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(cpp), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=5)


if __name__ == '__main__':
    unittest.main()
