#include "bubble_sound.hpp"
#include "brookesia/service_helper/media/audio.hpp"
#include <algorithm>
#include "esp_timer.h"
#include <vector>
namespace espocket {
namespace {
using Decoder = esp_brookesia::service::AudioDecoder;
using Playback = esp_brookesia::service::helper::AudioPlayback;
}
void BubbleSound::play(unsigned hz, unsigned ms)
{
    poll();
    try {
    if (source_ || hz == 0 || ms == 0 || ms > 130 || !Playback::is_available()) return;
    const auto mute = Playback::call_function_sync<bool>(Playback::FunctionId::GetMute,
        esp_brookesia::service::helper::Timeout(20));
    if (!mute || *mute) return;
    binding_ = esp_brookesia::service::ServiceManager::get_instance().bind("AudioDecoder0");
    auto *decoder = Decoder::get_instance(0);
    if (!binding_.is_valid() || !decoder) { close(); return; }
    auto outputs = decoder->get_outputs();
    auto found = std::find_if(outputs.begin(), outputs.end(), [](const auto &out) { return out.role == "speaker"; });
    if (found == outputs.end()) { close(); return; }
    output_ = found->name;
    auto registered = decoder->register_source({.name = "espocket.app.bubble_wrap.effect", .role = "effect",
        .preferred_outputs = {output_}, .priority = -100});
    if (!registered) { close(); return; }
    source_ = *registered;
    if (!decoder->request_output(*source_, output_)) { close(); return; }
    // Public native Owner seam checks/selects atomically. No check-then-steal race.
    if (!decoder->set_active_source(output_, "espocket.app.bubble_wrap.effect", true)) { close(); return; }
    esp_brookesia::service::AudioStreamConfig config;
    config.general = {.channels = 2, .sample_bits = 16, .sample_rate = 16000, .frame_duration = 20};
    config.queue_size_bytes = 12 * 1024;
    if (!decoder->open_stream(*source_, output_, config)) { close(); return; }
    // Original square wave; existing Audio volume/mute controls own output gain.
    const auto period = std::max(2U, 16000U / hz);
    auto samples = std::make_shared<std::vector<int16_t>>(ms * 16 * 2);
    for (size_t i = 0; i < samples->size() / 2; ++i)
        (*samples)[2 * i] = (*samples)[2 * i + 1] = i % period < period / 2 ? 5400 : -5400;
    released_at_us_ = std::make_shared<std::atomic<int64_t>>(0);
    duration_us_ = static_cast<int64_t>(ms) * 1000;
    auto result = decoder->write_stream_borrowed(*source_, output_,
        esp_brookesia::service::RawBuffer(samples->data(), samples->size() * sizeof(int16_t)),
        [samples, released = released_at_us_](auto result) {
            released->store(result == esp_brookesia::service::AudioWriteResult::Written ?
                std::max<int64_t>(1, esp_timer_get_time()) : -1, std::memory_order_release);
        }, 0);
    if (result != esp_brookesia::service::AudioWriteResult::Written) close();
    } catch (...) {
        // Optional sound must never strand an acquired source on allocation/service failure.
        close();
    }
}
void BubbleSound::poll()
{
    if (!source_) return;
    auto *decoder = Decoder::get_instance(0);
    const auto released = released_at_us_ ? released_at_us_->load(std::memory_order_acquire) : 0;
    // feed completion releases borrowed input; the HAL can still have output buffered.
    // Allow one tone duration asynchronously before closing, never wait on the App strand.
    if (!decoder || !binding_.is_valid() || released < 0 ||
        (released > 0 && esp_timer_get_time() - released >= duration_us_)) close();
}
void BubbleSound::close()
{
    auto *decoder = Decoder::get_instance(0);
    if (source_ && binding_.is_valid() && decoder) {
        (void)decoder->close_stream(*source_, output_);
        (void)decoder->release_output(*source_, output_);
        (void)decoder->unregister_source(*source_);
    }
    source_.reset(); released_at_us_.reset(); output_.clear(); binding_.release();
}
}
