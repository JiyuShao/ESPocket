"""Compile the real Card persistence adapter and preserve its existing raw JSON schema."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]


class CardStorageSchemaTest(unittest.TestCase):
    def test_raw_json_and_storage_failure(self):
        source = (ROOT / 'firmware/components/espocket_system/src/system_cards.cpp').read_text()
        start = source.index('std::expected<std::optional<std::string>, std::string> read_cards()')
        end = source.index('\n}\n}\n\nvoid System::init_cards()', start) + 2
        methods = source[start:end]
        code = r'''
#include <expected>
#include <optional>
#include <string>
#include <string_view>
#include <cassert>
#include "boost/json/src.hpp"
bool available = true, fail = false;
boost::json::object stored;
namespace esp_brookesia::service {
struct ServiceManager {
    struct Binding { bool is_valid() const { return available; } };
    static ServiceManager &get_instance() { static ServiceManager instance; return instance; }
    Binding bind(const char *) { return {}; }
};
namespace helper {
struct Timeout { int ms; explicit Timeout(int value) : ms(value) {} };
struct Storage {
    enum class FunctionId { KVGet, KVSet };
    static std::string_view get_name() { return "Storage"; }
    template<typename T> static std::expected<T, std::string> call_function_sync(
        FunctionId op, const std::string &ns, const boost::json::array &keys, Timeout timeout) {
        assert(op == FunctionId::KVGet && ns == "espocket" && keys.at(0) == "cards_v1" && timeout.ms == 5000);
        if (fail) return std::unexpected("io_failed");
        return stored;
    }
    static std::expected<void, std::string> call_function_sync(
        FunctionId op, const std::string &ns, const boost::json::object &values, Timeout timeout) {
        assert(op == FunctionId::KVSet && ns == "espocket" && timeout.ms == 5000);
        if (fail) return std::unexpected("io_failed");
        stored = values; return {};
    }
};
}}
constexpr char CARD_STORAGE_NAMESPACE[] = "espocket";
constexpr char CARD_STORAGE_KEY[] = "cards_v1";
using CardStorage = esp_brookesia::service::helper::Storage;
''' + methods + r'''
int main() {
    assert(read_cards() && !*read_cards());
    const std::string raw = R"({"version":1,"left":[],"right":[]})";
    stored["cards_v1"] = raw; // Existing device NVS value has no extra quotes.
    assert(**read_cards() == raw);
    assert(write_cards(raw));
    assert(stored.at("cards_v1").as_string() == raw);
    fail = true;
    assert(!write_cards("replacement") && !read_cards());
    assert(stored.at("cards_v1").as_string() == raw);
    fail = false;
    stored["cards_v1"] = false; assert(!read_cards());
    stored["cards_v1"] = std::string(16385, 'x'); assert(!read_cards());
    available = false; assert(!read_cards() && !write_cards(raw));
}
'''
        with tempfile.TemporaryDirectory() as directory:
            cpp, binary = Path(directory) / 'storage.cpp', Path(directory) / 'storage'
            cpp.write_text(code)
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-DBOOST_NO_USER_CONFIG',
                            '-I', str(ROOT / 'firmware/managed_components/espressif__esp-boost/src'),
                            str(cpp), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
