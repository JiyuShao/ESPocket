import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class AgentAudioQueueTest(unittest.TestCase):
    def exercise(self, component, directory):
        source = (component / 'src/base.cpp').read_text()
        method = source[source.index('bool Base::feed_audio_decoder_data('):source.index('bool Base::on_start()')]
        code = r'''
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <cstdint>
#include <cstdio>
#include <expected>
#include <functional>
#include <memory>
#include <mutex>
#include <span>
#include <string>
#include <vector>
#define BROOKESIA_LOGD(...)
#define BROOKESIA_LOGE(...)
#define BROOKESIA_LOGW(...)
#define BROOKESIA_DESCRIBE_TO_STR(value) "result"
namespace df { enum class AudioWriteResult { Written, DroppedQueueFull, Closed, Error }; }
constexpr const char *AGENT_AUDIO_OUTPUT_NAME = "speaker";
constexpr uint32_t AGENT_AUDIO_WRITE_TIMEOUT_MS = 20;
constexpr uint32_t AGENT_AUDIO_WRITE_COMPLETION_TIMEOUT_MS = 200;
struct Playback {
    bool available = true;
    size_t resets = 0;
    df::AudioWriteResult admission = df::AudioWriteResult::Written;
    std::vector<uint8_t> queued;
    std::function<void(df::AudioWriteResult)> pending_release;
    bool is_available() const { return available; }
    df::AudioWriteResult write_copy(const char *, std::span<const uint8_t> data, uint32_t timeout) {
        assert(timeout == 20);
        if (admission == df::AudioWriteResult::Written) queued.assign(data.begin(), data.end());
        return admission;
    }
    df::AudioWriteResult write_borrowed(const char *, std::span<const uint8_t>,
        std::function<void(df::AudioWriteResult)> release, uint32_t) {
        pending_release = std::move(release);
        if (admission != df::AudioWriteResult::Written) pending_release(admission);
        return admission;
    }
    std::expected<void, std::string> close_stream(const char *) {
        ++resets;
        if (pending_release) pending_release(df::AudioWriteResult::Error);
        queued.clear(); return {};
    }
    std::expected<void, std::string> open_stream(const char *, int) { return {}; }
};
enum class ChatMode { HalfDuplex, RealTime };
struct Base {
    std::shared_ptr<Playback> audio_playback_operation_ = std::make_shared<Playback>();
    bool disabled = false, listening = false;
    ChatMode mode = ChatMode::HalfDuplex;
    struct Config { int decoder = 0; } config;
    bool is_speaking_disabled() const { return disabled; }
    bool is_listening() const { return listening; }
    ChatMode get_chat_mode() const { return mode; }
    Config &get_audio_config() { return config; }
    int to_dataflow_audio_stream_config(int decoder) { return decoder; }
    bool feed_audio_decoder_data(const uint8_t *data, size_t data_size);
};
''' + method + r'''
int main() {
    Base agent;
    uint8_t packet[] = {0x78, 0x31, 0x42};
    auto started = std::chrono::steady_clock::now();
    if (!agent.feed_audio_decoder_data(packet, sizeof(packet))) {
        std::fprintf(stderr, "Deferred decoder consumption resets a healthy stream\n"); return 1;
    }
    assert(std::chrono::steady_clock::now() - started < std::chrono::milliseconds(100));
    packet[0] = 0;
    assert((agent.audio_playback_operation_->queued == std::vector<uint8_t>{0x78, 0x31, 0x42}));
    assert(agent.audio_playback_operation_->resets == 0);
    agent.audio_playback_operation_->close_stream(AGENT_AUDIO_OUTPUT_NAME);
    assert(agent.audio_playback_operation_->queued.empty());
    for (auto result : {df::AudioWriteResult::DroppedQueueFull, df::AudioWriteResult::Closed, df::AudioWriteResult::Error}) {
        agent.audio_playback_operation_->admission = result;
        assert(!agent.feed_audio_decoder_data(packet, sizeof(packet)));
        assert(agent.audio_playback_operation_->queued.empty());
    }
    agent.disabled = true;
    assert(agent.feed_audio_decoder_data(packet, sizeof(packet)));
    agent.disabled = false; agent.listening = true;
    assert(agent.feed_audio_decoder_data(packet, sizeof(packet)));
    agent.mode = ChatMode::RealTime;
    assert(!agent.feed_audio_decoder_data(packet, sizeof(packet)));
    agent.audio_playback_operation_->available = false;
    assert(!agent.feed_audio_decoder_data(packet, sizeof(packet)));
    agent.audio_playback_operation_.reset();
    assert(!agent.feed_audio_decoder_data(packet, sizeof(packet)));
}
'''
        harness = directory / 'queue.cpp'
        executable = directory / 'queue'
        harness.write_text(code)
        subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread',
                        str(harness), '-o', str(executable)], check=True)
        return subprocess.run([str(executable)], text=True, capture_output=True, timeout=5)

    def test_deferred_playback_owns_packets_without_resetting_stream(self):
        component = ROOT / 'firmware/managed_components/espressif__brookesia_agent_manager'
        with tempfile.TemporaryDirectory(prefix='espocket-agent-queue-') as temporary:
            directory = Path(temporary)
            original = self.exercise(component, directory)
            self.assertNotEqual(original.returncode, 0)
            self.assertIn('Deferred decoder consumption resets a healthy stream', original.stderr)
            patched = prepare(component, ROOT / 'firmware/patches/espressif__brookesia_agent_manager/0.8.2/manifest.json',
                              directory / 'patched')
            fixed = self.exercise(patched, directory)
            self.assertEqual(fixed.returncode, 0, fixed.stderr)
