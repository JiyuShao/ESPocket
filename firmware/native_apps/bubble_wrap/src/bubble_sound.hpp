#pragma once
#include <atomic>
#include "brookesia/service_audio/service_audio.hpp"
#include "brookesia/service_manager/service/manager.hpp"
namespace espocket {
// One short PCM stream through the existing Audio Owner. Busy output is skipped.
class BubbleSound {
public:
    ~BubbleSound() { close(); }
    void play(unsigned hz, unsigned ms);
    void poll();
    void close();
private:
    esp_brookesia::service::ServiceBinding binding_;
    std::optional<uint32_t> source_;
    std::string output_;
    std::shared_ptr<std::atomic<int64_t>> released_at_us_;
    int64_t duration_us_ = 0;
};
}
