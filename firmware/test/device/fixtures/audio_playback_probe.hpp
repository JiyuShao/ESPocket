#pragma once
// Temporary device fixture. Included only by prepare_audio_playback_probe.py in an isolated candidate.
#include <expected>
#include <string>
#include "esp_log.h"
#include "brookesia/service_helper/media/audio.hpp"
#include "brookesia/service_helper/system/storage.hpp"

extern const unsigned char probe_wav_start[] asm("_binary_espocket_audio_probe_wav_start");
extern const unsigned char probe_wav_end[] asm("_binary_espocket_audio_probe_wav_end");

namespace espocket::audio_probe {
using Audio = esp_brookesia::service::helper::AudioPlayback;
using Timeout = esp_brookesia::service::helper::Timeout;
using Storage = esp_brookesia::service::helper::Storage;
inline constexpr char path[] = "/littlefs/.espocket-audio-probe-v2.wav";
inline bool owns_file = false;
inline esp_brookesia::service::EventRegistry::SignalConnection state_connection;

inline std::expected<void, std::string> stop()
{
    if (!owns_file) return {};
    auto result = Audio::call_function_sync(Audio::FunctionId::Stop, Timeout(2000));
    if (!result) {
        ESP_LOGE("AUDIO-PROBE", "Stop failed; retaining fixture: %s", result.error().c_str());
        return result;
    }
    state_connection.disconnect();
    if (auto removed = Storage::fs_remove(path, 2000); !removed) {
        ESP_LOGE("AUDIO-PROBE", "Cleanup failed: %s", removed.error().c_str());
        return removed;
    }
    owns_file = false;
    ESP_LOGI("AUDIO-PROBE", "Stopped and removed owned fixture");
    return {};
}

inline std::expected<void, std::string> start()
{
    if (auto previous = stop(); !previous) return previous;
    // All Flash filesystem operations execute in the official Storage Owner's internal-RAM workers.
    // The Adapter serializes this single fixture; an unknown existing path is never replaced.
    auto info = Storage::fs_stat(path, 2000);
    if (!info) return std::unexpected(info.error());
    if (info->exists) return std::unexpected("unknown existing probe fixture; refusing replacement");
    const esp_brookesia::service::RawBuffer data(probe_wav_start, probe_wav_end - probe_wav_start);
    owns_file = true;
    auto written = Storage::fs_write(path, data, 2000);
    if (!written) {
        if (auto removed = Storage::fs_remove(path, 2000); removed) owns_file = false;
        return std::unexpected("Storage fixture write failed: " + written.error());
    }
    state_connection = Audio::subscribe_event(Audio::EventId::PlayStateChanged,
        [](const std::string &, const esp_brookesia::service::EventItemMap &items) {
            auto item = items.find("State");
            if (item != items.end()) {
                if (const auto *state = std::get_if<std::string>(&item->second))
                    ESP_LOGI("AUDIO-PROBE", "Owner state: %s", state->c_str());
            }
        });
    if (!state_connection.connected()) {
        if (auto removed = Storage::fs_remove(path, 2000); removed) owns_file = false;
        return std::unexpected("playback event subscription failed");
    }
    boost::json::object config{{"interrupt", true}, {"loop_count", 30}, {"timeout_ms", 35000}};
    auto played = Audio::call_function_sync(Audio::FunctionId::Play,
        std::string("file://littlefs/.espocket-audio-probe-v2.wav"), config, Timeout(2000));
    if (!played) {
        // Also stops a partially admitted asynchronous playback request before deleting the file.
        stop();
        return played;
    }
    ESP_LOGI("AUDIO-PROBE", "Submitted 400 Hz bounded playback; volume/mute unchanged");
    return {};
}
} // namespace espocket::audio_probe
